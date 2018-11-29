
from abc import ABC, abstractmethod
import threading
import zmq
import zmq.asyncio as zmqa
import pandas as pd
import numpy as np
from typing import Type
import struct
import asyncio

from ..async_agent import AsyncAgent
from ..event import QuoteEvent
from .. import const
from .. import utils


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
    def __init__(self, data_type: const.Data, broker: const.Broker, tickers, *args):
        super().__init__(*args)  # for multiple inheritance
        self.tickers = tickers

        self.type = data_type  # type: const.Data
        self.broker = broker  # type: const.Broker

        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.current_close = None

        self._now = None
        self.sid = ''
        self.queue = None

    @abstractmethod
    def update_bar(self):
        raise NotImplementedError('update_bar is not implemented')

    @abstractmethod
    def get_close(self, ticker):
        raise NotImplementedError('get_close is not implemented')

    def set_event_queue(self, sid, account_event_queue: asyncio.Queue):
        self.sid = sid
        self.queue = account_event_queue

    def set_time(self, timestamp):
        """
        for portfolio manager
        """
        pass

    @abstractmethod
    def set_look_back(self, period=0):
        raise NotImplementedError('set_loopback is not implemented')

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
        super(HistoricalDataObject, self).__init__(const.Data.SIMULATED, const.Broker.SIMULATED, tickers)

        self.__data = data
        self.index_row = 0
        self.prev_row = 0
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

        self.index_row += 1
        self._update_bar()
        return True

    def set_look_back(self, period=0):
        if self.index_row < period:
            self.index_row = period  # set start point to lookback period
        self._update_bar()

    async def set_time(self, timestamp):
        while self.index_row < self.last_row and timestamp >= self.__timestamps[self.index_row]:
            self.index_row += 1
        await self._update_and_quote()

    def get_close(self, ticker):
        return self.current_close[ticker]

    async def _update_and_quote(self):
        self._update_bar()
        await self.send_quotes()
        self.prev_row = self.index_row

    def _update_bar(self):
        self._now = self.__timestamps[self.index_row - 1]
        self.open = self.__open[:self.index_row]
        self.high = self.__high[:self.index_row]
        self.low = self.__low[:self.index_row]
        self.close = self.__close[:self.index_row]
        self.current_close = {ticker: price for ticker, price in zip(self.tickers, self.close[-1])}

    async def send_quotes(self):
        for idx in range(self.prev_row, self.index_row):
            await self.queue.put(QuoteEvent(self.__timestamps[idx], self.sid,
                                            {ticker: price for ticker, price in zip(self.tickers, self.close[idx])}))


class RealTimeDataObject(DataObject, AsyncAgent):
    def __init__(self, tickers, data=None):
        super(RealTimeDataObject, self).__init__(tickers)

        self.bars = {ticker: Bar() for ticker in tickers}
        self.data_ready = threading.Event()
        self.agent_close = threading.Event()
        self.events = [self.data_ready, self.agent_close]
        self.look_back = None

        self.__open = []
        self.__high = []
        self.__low = []
        self.__close = []
        self.__prices = [self.__open, self.__high, self.__low, self.__close]

        config = utils.load_config()
        self.socket = zmqa.Context().socket(zmq.SUB)
        # sub needs to subscribe to topic
        for ticker in tickers:
            self.socket.setsockopt(zmq.SUBSCRIBE, ticker.encode())
        self.socket.connect(f'tcp://127.0.0.1:{config["data_server_broadcast_port"]}')
        self.run_in_fork()

    def _run(self):
        return [
            [self.collect_data, '']
        ]

    def set_look_back(self, period=0):
        self.look_back = period

    def update_bar(self):
        self.data_ready.wait()
        self.data_ready.clear()

        # data_ready can be set because of agent shutdown, need to check specifically
        if not self.agent_close.is_set():
            ohlc = [self.bars[ticker].get() for ticker in self.tickers]
            ohlc = list(map(list, zip(*ohlc)))  # transpose
            for datum, price in zip(self.__prices, ohlc):
                if len(datum) >= self.look_back:
                    datum.pop(0)
                datum.append(price)

            self.open = np.array(self.__open)
            self.high = np.array(self.__high)
            self.low = np.array(self.__low)
            self.close = np.array(self.__close)
            return True
        return False

    def get_close(self, ticker):
        pass

    async def collect_data(self):
        [ticker, msg] = await self.socket.recv_multipart()
        ticker = ticker.decode()
        timestamp, price = struct.unpack('if', msg)
        print(timestamp, price)
        self.bars[ticker].add(price)

        if timestamp % 5 == 0:
            self.data_ready.set()
            if self.queue is not None:
                await self.queue.put(QuoteEvent(timestamp,
                                                {ticker: self.bars[ticker].close for ticker in self.tickers}))
