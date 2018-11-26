
import asyncio
import zmq
import zmq.asyncio as zmqa
from typing import Dict, Union, List
import pickle

from ..async_agent import AsyncAgent
from ..data import DataObject
from ..portfolio import TradeRecord
from ..event import OrderEvent, FillEvent, QuoteEvent, AccountOpenEvent, AccountCloseEvent, SignalEvent
from ..execution import OrderType
from .. import utils
from .. import const


class Account:
    def __init__(self, timestamp, data_obj: DataObject, capital=10000):
        self.position = TradeRecord(timestamp, capital, data_obj.tickers)
        self.broker = data_obj.broker
        self.data_obj = data_obj


class PortfolioManager(AsyncAgent):
    def __init__(self, config_file=None):
        super().__init__()

        config = utils.load_config(config_file)
        self.account_port = config['manager_request_port']
        self.order_port = config['manager_order_port']
        self.data_port = config['data_server_request_port']

        self.accounts = {}  # type: Dict[str, Account]
        self.brokers = {
            const.Broker.SIMULATED: asyncio.Queue()
        }
        self.account_events = asyncio.Queue()

        self.socket = zmqa.Context().socket(zmq.ROUTER)
        self.socket.bind(f'tcp://127.0.0.1:{self.account_port}')

        self.order_socket = zmqa.Context().socket(zmq.ROUTER)
        self.order_socket.bind(f'tcp://127.0.0.1:{self.order_port}')

        self.data_socket = zmqa.Context().socket(zmq.REQ)
        self.data_socket.connect(f'tcp://127.0.0.1:{self.data_port}')

    def _run(self):
        return [
            [self.handle_account_request,   f'Starting listening on port {self.account_port}'],
            [self.handle_order_request,     f'Starting listening for order on port {self.order_port}'],

            [self.handle_account_event,     ''],
            [self.execute_simulated_order,  '']
         ]

    async def handle_account_request(self):
        [pid, event] = await self.socket.recv_multipart()
        event = pickle.loads(event)  # type: Union[AccountOpenEvent, AccountCloseEvent]

        if event.type == const.Event.ACCT_OPEN:  # create new account
            print(f'Received request: {event.data_request} for {event.sid}')

            if event.sid in self.accounts:
                raise ValueError(f'Account {event.sid} already exists')

            await self.data_socket.send_pyobj(event.data_request)
            dispatcher = await self.data_socket.recv_pyobj()

            data_obj = dispatcher.dispatch()  # type: DataObject
            data_obj.set_event_queue(event.sid, self.account_events)
            self.accounts[event.sid] = Account(event.timestamp, data_obj, event.capital)

            await self.socket.send_multipart([pid, pickle.dumps(dispatcher)])
            print(f'Account "{event.sid}" created')

        elif event.type == const.Event.ACCT_CLOSE:  # close account
            self.socket.send_multipart([pid, pickle.dumps(self.accounts[event.sid].position)])
            del self.accounts[event.sid]
            print(f'Account "{event.sid}" closed')

        else:
            raise ValueError(f'Unrecognized request type {event.type}')

    async def handle_order_request(self):
        pid, signal = await self.order_socket.recv_multipart()
        signal = pickle.loads(signal)  # type: SignalEvent
        print(signal.signal)

        if signal.sid not in self.accounts:
            raise ValueError(f'Account {signal.sid} not exists')
        account = self.accounts[signal.sid]  # type: Account

        if account.broker == const.Broker.SIMULATED:
            await account.data_obj.set_time(signal.timestamp)  # this is to synchronize time with the data object

        position = self.accounts[signal.sid].position
        unit_capital = position.get_equity() / sum([abs(x) for x in signal.signal.values()])

        buy_orders = []
        sell_orders = []  # we want to sell the position first because it releases capital
        for ticker, alpha in signal.signal.items():
            pos = int(alpha * unit_capital / account.data_obj.get_close(ticker))
            delta = pos - position[ticker]
            if delta > 0:
                buy_orders.append([delta, pos, ticker])
            elif delta < 0:
                sell_orders.append([delta, pos, ticker])

        for orders in [buy_orders, sell_orders]:
            if len(orders):
                to_execute = [OrderEvent(signal.sid, ticker, OrderType.LMT, qty) for qty, _, ticker in orders]
                # await self.brokers[account.broker].put(to_execute)

            for quantity, pos, ticker in orders:
                print(f'{signal.sid}: {ticker} ({position[ticker]} -> {pos})')

    async def handle_account_event(self):
        event = await self.account_events.get()  # type: Union[FillEvent, QuoteEvent]
        if event.type == const.Event.FILL:
            print(event)
            self.accounts[event.sid].position.update(event.ticker, event.quantity, event.price, event.commission)
            print(self.accounts[event.sid].position)
        elif event.type == const.Event.QUOTE:
            self.accounts[event.sid].position.take_snapshot(event.timestamp, event.quotes)
        else:
            raise ValueError(f'Unrecognized event type {type(event)}')

    async def execute_simulated_order(self):
        orders = await self.brokers[const.Broker.SIMULATED].get()  # type: List[OrderEvent]
        for order in orders:
            data = self.accounts[order.sid].data_obj
            await self.account_events.put(FillEvent(data.now, order.sid, order.ticker, const.Broker.SIMULATED,
                                                    order.quantity, data.get_close(order.ticker)))
