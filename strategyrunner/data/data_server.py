
import zmq
import zmq.asyncio as zmqa
import asyncio
from concurrent import futures
import pickle
import os
import struct

from ..async_agent import AsyncAgent
from ..data import DataManager, HistoricalDataObject, RealTimeDataObject, Dispatcher
from ..event import DataRequestEvent
from .. import utils
from .. import const


class Request:
    def __repr__(self):
        return self.__str__()


class HistoricalDataRequest(Request):
    def __init__(self, tickers: list, start_date, end_date):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return f'Request {", ".join(self.tickers)} historical data from {self.start_date} to {self.end_date}'


class RealTimeDataRequest(Request):
    def __init__(self, tickers: list):
        self.tickers = tickers

    def __str__(self):
        return f'Request {", ".join(self.tickers)} real-time data'


class DataServer(AsyncAgent):
    def __init__(self, config_file=None):
        super().__init__()

        config = utils.load_config(config_file)
        self.request_port = config['data_server_request_port']
        self.pub_port = config['data_server_broadcast_port']
        self.db_dir = f'{os.getcwd()}/data/test.db'

        self.socket = zmqa.Context().socket(zmq.ROUTER)
        self.socket.bind(f'tcp://127.0.0.1:{self.request_port}')
        self.broadcast_socket = zmqa.Context().socket(zmq.PUB)
        self.broadcast_socket.bind(f'tcp://127.0.0.1:{self.pub_port}')

        self.executor = futures.ThreadPoolExecutor(max_workers=10)
        self.tickers = set()
        self.counter = 0

        self.run_coroutine(f'Listening on port {self.request_port}', self.handle_data_request)
        self.run_coroutine(f'Broadcasting started on port {self.pub_port}', self.broadcast_data)

    async def handle_data_request(self):
        pid, _, request = await self.socket.recv_multipart()
        event = pickle.loads(request)
        print(f'Request received from {pid}: {event}')
        self.run_coroutine('', self.send_data_obj, pid, event)
        return True

    async def send_data_obj(self, cid: bytes, event: DataRequestEvent):
        if event.broker == const.Broker.SIMULATED:  # historical data
            print(f'Loading historical data for {event.tickers} from {event.start_time} to {event.end_time}')
            data = await self.loop.run_in_executor(self.executor, self.retrieve_data_from_db,
                                                   event.tickers, event.start_time, event.end_time)
            data_obj = Dispatcher(HistoricalDataObject, event.tickers, data=data)

        elif event.broker == const.Broker.INTERACTIVE_BROKERS:  # IB real time data
            self.tickers |= set(event.tickers)
            print('Enlisted tickers: ', self.tickers)
            data_obj = Dispatcher(RealTimeDataObject, event.tickers)

        else:
            raise ValueError('Unrecognized request')
        await self.socket.send_multipart([cid, b'', pickle.dumps(data_obj)])
        print('Data object sent')

    async def broadcast_data(self):
        self.counter += 1
        for ticker in self.tickers:
            await self.broadcast_socket.send_multipart([ticker.encode(), struct.pack('if', *[self.counter, self.counter])])
        await asyncio.sleep(1)
        return True

    def retrieve_data_from_db(self, tickers, start_date, end_date):
        with DataManager(self.db_dir) as dm:
            data = dm.get_data(tickers, start_date, end_date)
        return data
