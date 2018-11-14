
from abc import ABC, abstractmethod
import threading
import zmq
import zmq.asyncio as zmqa
import pandas as pd
import numpy as np
from typing import Type
import struct

from strategyrunner.async_agent import AsyncAgent


class Bar:
    def __init__(self):
        self.open = None
        self.high = None
        self.low = None
        self.close = None

    def add(self, price):
        if self.open is None:
            self.open = price
        self.high = max(self.high, price) if self.high is not None else price
        self.low = min(self.low, price) if self.low is not None else price
        self.close = price

    def get(self):
        tmp = [self.open, self.high, self.low, self.close].copy()
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        return tmp


class DataObject(ABC):
    def __init__(self, tickers, data=None, *args):
        super().__init__(*args)  # for multiple inheritance
        self.tickers = tickers
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self._now = None
        self.current_close = None

    @abstractmethod
    def update_bar(self):
        raise NotImplementedError('update_bar is not implemented')

    @property
    def now(self):
        return self._now


class Dispatcher:
    def __init__(self, data_class: Type[DataObject], tickers: list, data=None):
        if data_class is HistoricalDataObject:
            if data is None:
                raise ValueError('Data is not provided for Historical Data Object')

        self.data_class = data_class
        self.tickers = tickers
        self.data = data

    def dispatch(self):
        if self.data_class is HistoricalDataObject:
            return self.data_class(self.tickers, self.data)
        elif self.data_class is RealTimeDataObject:
            return self.data_class(self.tickers)
        else:
            raise ValueError('Unrecognized data object class')


class HistoricalDataObject(DataObject):
    def __init__(self, tickers, data: pd.DataFrame):
        super(HistoricalDataObject, self).__init__(tickers)

        self.__data = data
        self.index_row = 0
        self.last_row = self.__data.shape[0]

        # since loc in this case returns copy, we do indexing once and for all to avoid overhead
        self.tickers = self.__data.close.columns.tolist()  # update tickers to ensure order
        self.__open = self.__data.open.values
        self.__high = self.__data.high.values
        self.__low = self.__data.low.values
        self.__close = self.__data.close.values
        self.__timestamps = self.__data.index.tolist()

    def update_bar(self):
        # end of data
        if self.index_row >= self.last_row:
            return False

        # populate new data
        self._now = self.__timestamps[self.index_row]  # n - 1
        self.index_row += 1
        self.open = self.__open[:self.index_row]
        self.high = self.__high[:self.index_row]
        self.low = self.__low[:self.index_row]
        self.close = self.__close[:self.index_row]
        self.current_close = {ticker: price for ticker, price in zip(self.tickers, self.close[-1])}
        return True


class RealTimeDataObject(DataObject, AsyncAgent):
    def __init__(self, tickers, cache=5, port=4001):
        super().__init__(tickers)

        self.bars = {ticker: Bar() for ticker in tickers}
        self.cache = cache
        self.data_ready = threading.Event()
        self.agent_close = threading.Event()
        self.events = [self.data_ready, self.agent_close]

        self.__open = []
        self.__high = []
        self.__low = []
        self.__close = []
        self.__prices = [self.__open, self.__high, self.__low, self.__close]

        self.socket = zmqa.Context().socket(zmq.SUB)
        # sub needs to subscribe to topic
        for ticker in tickers:
            self.socket.setsockopt(zmq.SUBSCRIBE, ticker.encode())
        self.socket.connect(f'tcp://127.0.0.1:{port}')
        self.run_in_fork()

    def update_bar(self):
        self.data_ready.wait()
        self.data_ready.clear()

        # data_ready can be set because of agent shutdown, need to check specifically
        if not self.agent_close.is_set():
            ohlc = [self.bars[ticker].get() for ticker in self.tickers]
            ohlc = list(map(list, zip(*ohlc)))  # transpose
            for datum, price in zip(self.__prices, ohlc):
                if len(datum) >= self.cache:
                    datum.pop(0)
                datum.append(price)

            self.open = np.array(self.__open)
            self.high = np.array(self.__high)
            self.low = np.array(self.__low)
            self.close = np.array(self.__close)
            return True
        return False

    async def collect_data(self):
        while True:
            [ticker, msg] = await self.socket.recv_multipart()
            ticker = ticker.decode()
            timestamp, price = struct.unpack('if', msg)
            print(timestamp, price)
            self.bars[ticker].add(price)

            if timestamp % 5 == 0:
                self.data_ready.set()

    def _run(self):
        return [self.collect_data()]
