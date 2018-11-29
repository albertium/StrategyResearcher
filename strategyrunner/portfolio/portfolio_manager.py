
import asyncio
import zmq
import zmq.asyncio as zmqa
from typing import Dict, Union
import pickle
from collections import deque

from ..async_agent import AsyncAgent
from ..data import DataObject
from ..portfolio import TradeRecord
from ..event import OrderEvent, FillEvent, QuoteEvent, AccountOpenEvent, AccountCloseEvent, SignalEvent, BaseEvent
from ..helpers import Counter
from .. import utils
from .. import const


class Account:
    def __init__(self, timestamp, data_obj: DataObject, capital=10000):
        self.position = TradeRecord(timestamp, capital, data_obj.tickers)
        self.broker = data_obj.broker
        self.data_obj = data_obj
        self.count = 0  # for checking if fills are completed


class BatchedQueue:
    def __init__(self):
        self.sids = {}
        self.queues = {}
        self._signal_ready = Counter()
        self._queue_ready = Counter()

    def put(self, signal: BaseEvent):
        print(f'added {signal}')
        self.queues.setdefault(signal.sid, deque()).append(signal)
        self._signal_ready.inc()

    def set_ready(self, sid):
        self.sids[sid] = True
        self._queue_ready.inc()

    def delete(self, sid):
        del self.sids[sid]
        del self.queues[sid]

    async def get(self):
        await self._signal_ready.wait()
        await self._queue_ready.wait()

        print(f'items: {self.queues}')

        for sid, queue in self.queues.items():
            if self.sids[sid] is True and queue:
                value = queue.popleft()
                self._signal_ready.dec()
                self._queue_ready.dec()
                self.sids[sid] = False
                return value


class PortfolioManager(AsyncAgent):
    def __init__(self, config_file=None):
        super().__init__()

        config = utils.load_config(config_file)
        self.port = config['manager_request_port']
        self.data_port = config['data_server_request_port']

        self.accounts = {}  # type: Dict[str, Account]
        self.account_queues = {}  # type: Dict[str, asyncio.Queue]
        self.feedbacks = {}  # type: Dict[str, asyncio.Queue]
        self.event_queue = asyncio.Queue()
        self.brokers = {
            const.Broker.SIMULATED: asyncio.Queue()
        }

        self.socket = zmqa.Context().socket(zmq.ROUTER)
        self.socket.bind(f'tcp://127.0.0.1:{self.port}')

        self.data_socket = zmqa.Context().socket(zmq.REQ)
        self.data_socket.connect(f'tcp://127.0.0.1:{self.data_port}')

        self.run_coroutine(f'Starting listening on port {self.port}', self.handle_request)
        self.run_coroutine('', self.handle_events)
        self.run_coroutine('', self.execute_simulated_order)

    def _run(self):
        return []

    async def handle_request(self):
        [pid, event] = await self.socket.recv_multipart()
        event = pickle.loads(event)  # type: Union[AccountOpenEvent, AccountCloseEvent]

        if event.type == const.Event.ACCT_OPEN:  # create new account
            print(f'Received request: {event.data_request} for {event.sid}')

            if event.sid in self.accounts:
                raise ValueError(f'Account {event.sid} already exists')

            event.pid = pid  # for sending data object
            self.account_queues[event.sid] = asyncio.Queue()
            self.feedbacks[event.sid] = asyncio.Queue()
            self.run_coroutine('', self.handle_strategy_event, self.account_queues[event.sid], self.feedbacks[event.sid])

        elif event.type == const.Event.ACCT_CLOSE:  # close account
            event.pid = pid  # for sending record

        await self.account_queues[event.sid].put(event)
        return True

    async def handle_strategy_event(self, queue: asyncio.Queue, feedback: asyncio.Queue):
        event = await queue.get()  # type: Union[AccountOpenEvent, SignalEvent]
        if event.type != const.Event.SIGNAL:
            print(event)

        if event.type == const.Event.ACCT_OPEN:
            await self.data_socket.send_pyobj(event.data_request)
            dispatcher = await self.data_socket.recv_pyobj()
            data_obj = dispatcher.dispatch()  # type: DataObject

            data_obj.set_event_queue(event.sid, self.event_queue)
            self.accounts[event.sid] = Account(event.timestamp, data_obj, event.capital)

            await self.socket.send_multipart([event.pid, pickle.dumps(dispatcher)])
            print(f'Account "{event.sid}" created')

        elif event.type == const.Event.SIGNAL:
            if event.sid not in self.accounts:
                raise ValueError(f'Account {event.sid} not exists')

            # for simulated data, synchronize timestamp and send t-1 quote events to outside loop
            if self.accounts[event.sid].broker == const.Broker.SIMULATED:
                await self.accounts[event.sid].data_obj.set_time(event.timestamp)

            await self.event_queue.put(event)
            order = await feedback.get()  # type: OrderEvent

            if order.added():
                position = self.accounts[event.sid].position

                print('############# PLAN #############')
                for ticker, (_, delta) in order.orders.items():
                    print(f'{order.sid}: {ticker} ({position[ticker]} -> {position[ticker] + delta})')
                print('################################\n')

                await self.event_queue.put(order)
                filled = await feedback.get()
                print(filled)
                position.update_from_fill(filled)

        elif event.type == const.Event.ACCT_CLOSE:
            self.socket.send_multipart([event.pid, pickle.dumps(self.accounts[event.sid].position)])
            del self.accounts[event.sid]
            print(f'Account "{event.sid}" closed')
            return False

        else:
            raise ValueError(f'Unrecognized event type {event.type.name}')

        return True

    async def handle_events(self):
        event = await self.event_queue.get()  # type: Union[SignalEvent, FillEvent, QuoteEvent]
        print(event)

        if event.type == const.Event.QUOTE:
            self.accounts[event.sid].position.take_snapshot(event.timestamp, event.quotes)

        elif event.type == const.Event.SIGNAL:
            # convert signal to order
            position = self.accounts[event.sid].position
            data = self.accounts[event.sid].data_obj
            unit_capital = position.get_equity() / sum([abs(x) for x in event.signal.values()])

            order = OrderEvent(event.timestamp, event.sid)
            buy_orders = []
            for ticker, alpha in event.signal.items():
                pos = int(alpha * unit_capital / data.get_close(ticker))
                delta = pos - position[ticker]
                if delta < 0:
                    # we want to sell positions first because that releases capital
                    order.add(ticker, const.Order.LMT, delta)
                elif delta > 0:
                    buy_orders.append([ticker, pos, delta])

            # add remaining buy orders
            for ticker, pos, delta in buy_orders:
                order.add(ticker, const.Order.LMT, delta)

            await self.feedbacks[event.sid].put(order)

        elif event.type == const.Event.ORDER:
            await self.brokers[self.accounts[event.sid].broker].put(event)

        else:
            raise ValueError(f'Unrecognized event type {event.type.name}')

        return True

    async def execute_simulated_order(self):
        order = await self.brokers[const.Broker.SIMULATED].get()  # type: OrderEvent
        data = self.accounts[order.sid].data_obj
        fill = FillEvent(order.timestamp, order.sid)
        for ticker, (_, qty) in order.orders.items():
            fill.add(ticker, data.get_close(ticker), qty)

        await self.feedbacks[order.sid].put(fill)
        return True
