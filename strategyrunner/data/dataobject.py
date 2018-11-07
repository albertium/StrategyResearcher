
from abc import ABC, abstractmethod
import zmq
import pandas as pd

from strategyrunner.async_agent import AsyncAgent


class DataObject(ABC):
    def __init__(self, data_source):
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.current_close = None

    @abstractmethod
    def update_bar(self):
        raise NotImplementedError('update_bar is not implemented')


class HistoricalDataObject(DataObject):
    def __init__(self, data_source: pd.DataFrame):
        super().__init__(data_source)

        self.__data = data_source
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
    def __init__(self, data_source):
        super().__init__(data_source)

    async def update_bar(self):
        price = await self._update_bar()
        print(price)

    async def _update_bar(self):
        pass