
from .data_handler import DataHandler
from .data_manager import DataManager
from ..event import MarketEvent
from queue import Queue
from typing import List


class HistoricalDataHandler(DataHandler):
    def __init__(self, events: Queue, tickers: List, start_date, end_date):
        super().__init__(events, tickers, start_date, end_date)

        with DataManager("data/test.db") as dm:
            self.__data = dm.get_data(tickers, start_date, end_date)

        self.last_row = self.__data.shape[0]
        self.index_row = 0

        # since loc in this case returns copy, we do indexing once and for all to avoid overhead
        self.__open = self.__data.loc[:, "open"]
        self.__high = self.__data.loc[:, "high"]
        self.__low = self.__data.loc[:, "low"]
        self.__close = self.__data.loc[:, "close"]

    def update_bar(self):
        # end of data
        if self.index_row >= self.last_row:
            return False

        self.index_row += 1

        # populate new data
        self.open = self.__open.iloc[:self.index_row, :]
        self.high = self.__high.iloc[:self.index_row, :]
        self.low = self.__low.iloc[:self.index_row, :]
        self.close = self.__close.iloc[:self.index_row, :]
        self.events.put(MarketEvent())
        return True
