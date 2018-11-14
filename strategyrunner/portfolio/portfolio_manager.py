
import asyncio
import zmq
import zmq.asyncio as zmqa
import json
import struct
import pickle

from strategyrunner.async_agent import AsyncAgent
from strategyrunner.portfolio import TradeRecord
from strategyrunner.event import OrderEvent
from strategyrunner.execution import OrderType


class Account:
    def __init__(self, position, data_obj=None):
        self.position = position
        self.data_obj = data_obj


class PortfolioManager(AsyncAgent):
    def __init__(self, port=4002):
        super().__init__()

        self.accounts = {}
        self.order_to_execute = asyncio.Queue()

        self.port = port
        self.socket = zmqa.Context().socket(zmq.ROUTER)
        self.socket.connect(f'tcp://127.0.0.1:{port}')

    def _run(self):
        return [self.handle_request()]

    async def handle_request(self):
        print(f'Starting listening on port {self.port}')
        [timestamp, sid, request_type, request, data_obj] = await self.socket.recv_multipart()
        timestamp, sid, request = sid.decode(), struct.unpack('i', timestamp), json.loads(request.decode())

        if request_type in [b'NR', b'NB']:  # new real account / backtest account
            if sid in self.accounts:
                print('Account already exists')
            elif request_type == b'NB':
                self.accounts[sid] = Account(TradeRecord(timestamp, request['init'], request['tickers']),
                                             pickle.loads(data_obj))
            elif request_type == b'NR':
                self.accounts[sid] = Account(TradeRecord(timestamp, request['init'], request['tickers']))

        elif request_type == b'O':  # new order
            position = self.accounts[sid].position
            data_obj = self.accounts[sid].data_obj  # todo: real time is not handled yet, in which data should be requested real-time
            unit_capital = position.get_equity() / sum([abs(x) for x in request.values()])

            buy_orders = []
            sell_orders = []  # we want to sell the position first because it releases capital
            for ticker, alpha in request.items():
                pos = int(alpha * unit_capital / data_obj.get_close(ticker))
                delta = pos - position[ticker]
                if delta > 0:
                    buy_orders.append([delta, pos, ticker])
                elif delta < 0:
                    sell_orders.append([delta, pos, ticker])

            for orders in [buy_orders, sell_orders]:
                if len(orders):
                    to_execute = [OrderEvent(sid, ticker, OrderType.LMT, qty) for qty, _, ticker in orders]
                    await self.order_to_execute.put(to_execute)

                for quantity, pos, ticker in orders:
                    print(f'{sid}: {ticker} ({position[ticker]} -> {pos})')

        else:
            print(f'Unrecognized request type {request_type} from {sid}')

    async def execute_order(self):
        orders = await self.order_to_execute.get()
        fill = FillEvent(self.data.now(), event.strategy_id, event.ticker, "SIM", event.quantity,
                         self.data.get_close(event.ticker))
        self.events.put(fill)



