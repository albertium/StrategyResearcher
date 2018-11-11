
import zmq
import zmq.asyncio as zmqa
import asyncio
from concurrent import futures
import pickle
import os
import struct

from strategyrunner.async_agent import AsyncAgent
from strategyrunner.data import DataManager, HistoricalDataObject, RealTimeDataObject, Dispatcher


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
    def __init__(self):
        super().__init__()

        self.router_port = 4000
        self.pub_port = 4001
        self.db_dir = f'{os.getcwd()}/test.db'

        self.socket = zmqa.Context().socket(zmq.ROUTER)
        self.socket.bind(f'tcp://127.0.0.1:{self.router_port}')
        self.broadcast_socket = zmqa.Context().socket(zmq.PUB)
        self.broadcast_socket.bind(f'tcp://127.0.0.1:{self.pub_port}')

        self.executor = futures.ThreadPoolExecutor(max_workers=10)
        self.tickers = set()
        self.counter = 0

    async def handle_data_request(self):
        print(f'Listening on port {self.router_port}')

        while True:
            [cid, _, request] = await self.socket.recv_multipart()
            print('alive')
            request = pickle.loads(request)
            print(f'{cid} request received: {request}')
            asyncio.ensure_future(self.handle_exception(self.send_data_obj(cid, request)))

    async def send_data_obj(self, cid: bytes, request: Request):
        if isinstance(request, HistoricalDataRequest):
            data = await self.loop.run_in_executor(self.executor, self.retrieve_data_from_db,
                                                       request.tickers, request.start_date, request.end_date)
            data_obj = Dispatcher(HistoricalDataObject, request.tickers, data=data)
        elif isinstance(request, RealTimeDataRequest):
            self.tickers |= set(request.tickers)
            print('Enlisted tickers: ', self.tickers)
            data_obj = Dispatcher(RealTimeDataObject, request.tickers)
        else:
            raise ValueError('Unrecognized request')
        await self.socket.send_multipart([cid, b'', pickle.dumps(data_obj)])
        print('Data object sent')

    async def broadcast_data(self):
        print(f'Broadcasting started on port {self.pub_port}')
        while True:
            self.counter += 1
            for ticker in self.tickers:
                await self.broadcast_socket.send_multipart([ticker.encode(), struct.pack('if', *[self.counter, self.counter])])
            await asyncio.sleep(1)

    def retrieve_data_from_db(self, tickers, start_date, end_date):
        with DataManager(self.db_dir) as dm:
            data = dm.get_data(tickers, start_date, end_date)
        return data

    def _run(self):
        return [self.handle_data_request(), self.broadcast_data()]
