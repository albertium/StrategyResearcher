
import asyncio
import zmq
import zmq.asyncio as zmqa
import json
from typing import Dict
import pickle

from strategyrunner.async_agent import AsyncAgent
from strategyrunner.portfolio import TradeRecord
from strategyrunner.event import OrderEvent, FillEvent, QuoteEvent
from strategyrunner.execution import OrderType
from strategyrunner import utils
from strategyrunner import const
from .. import message


class Account:
    def __init__(self, position: TradeRecord, broker, data_obj):
        self.position = position
        self.broker = broker
        self.data_obj = data_obj


class PortfolioManager(AsyncAgent):
    def __init__(self, config_file=None):
        super().__init__()

        config = utils.load_config(config_file)
        self.account_port = config['manager_request_port']
        self.order_port = config['manager_order_port']
        self.data_port = config['data_server_request_port']

        self.accounts = {}  # type: Dict[str, Account]
        self.exchanges = {
            'Simulated': asyncio.Queue()
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
        [pid, req] = await self.socket.recv_multipart()
        req = json.loads(req.decode())

        if req['type'] == 'C':  # create new account
            timestamp, sid, capital, data_req = message.parse_acct_create_msg(req)
            print(f'Received request {data_req} from {sid}')

            if sid in self.accounts:
                raise ValueError(f'Account {sid} already exists')

            await self.data_socket.send_json(req['data'])  # pass raw request, not the parsed one
            dispatcher = await self.data_socket.recv_pyobj()

            data_obj = dispatcher.dispatch()
            self.accounts[sid] = Account(TradeRecord(timestamp, capital, data_req['tickers']), data_req['src'], data_obj)

            await self.socket.send_multipart([pid, pickle.dumps(dispatcher)])
            print(f'Account "{sid}" created')

        elif req['type'] == 'F':  # close account
            _, sid = message.parse_acct_finish_msg(req)
            self.socket.send_multipart([pid, pickle.dumps(self.accounts[sid].position)])
            del self.accounts[sid]
            print(f'Account "{sid}" closed')

        else:
            raise ValueError(f'Unrecognized request type {req["type"]}')

    async def handle_order_request(self):
        pid, msg = await self.order_socket.recv_multipart()
        timestamp, sid, raw_order = message.parse_order_msg(json.loads(msg.decode()))
        print(raw_order)

        if sid not in self.accounts:
            raise ValueError(f'Account {sid} not exists')
        account = self.accounts[sid]  # type: Account

        if account.broker == 'Simulated':
            account.data_obj.set_time(timestamp)  # this is to synchronize time with the data object

        position = self.accounts[sid].position
        unit_capital = position.get_equity() / sum([abs(x) for x in raw_order.values()])

        buy_orders = []
        sell_orders = []  # we want to sell the position first because it releases capital
        for ticker, alpha in raw_order.items():
            pos = int(alpha * unit_capital / account.data_obj.get_close(ticker))
            delta = pos - position[ticker]
            if delta > 0:
                buy_orders.append([delta, pos, ticker])
            elif delta < 0:
                sell_orders.append([delta, pos, ticker])

        for orders in [buy_orders, sell_orders]:
            if len(orders):
                to_execute = [OrderEvent(sid, ticker, OrderType.LMT, qty) for qty, _, ticker in orders]
                await self.exchanges[account.broker].put(to_execute)

            for quantity, pos, ticker in orders:
                print(f'{sid}: {ticker} ({position[ticker]} -> {pos})')

    async def handle_account_event(self):
        event = await self.account_events.get()
        if isinstance(event, FillEvent):
            print(event)
            self.accounts[event.sid].position.update(event.ticker, event.quantity, event.price, event.commission)
        elif isinstance(event, QuoteEvent):
            self.accounts[event.sid].position.take_snapshot(event.timestamp, event.quotes)
        else:
            raise ValueError(f'Unrecognized event type {type(event)}')

    async def execute_simulated_order(self):
        orders = await self.exchanges['Simulated'].get()
        for order in orders:
            data = self.accounts[order.sid].data_obj
            await self.account_events.put(FillEvent(data.now(), order.strategy_id, order.ticker, "Simulated",
                                                    order.quantity, data.get_close(order.ticker)))
