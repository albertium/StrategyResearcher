
from .data_handler import DataHandler
from .data_manager import DataManager
from ..event import MarketEvent
from ..logging import Logger
from queue import Queue
from typing import List
import time


class HistoricalDataHandler(DataHandler):
    def __init__(self, logger: Logger, events: Queue, tickers: List, start_date, end_date):
        super().__init__(logger, events, tickers, start_date, end_date)

        try:
            with DataManager("data/test.db") as dm:
                self.__data = dm.get_data(tickers, start_date, end_date)
                aaa = self.__data
        except ValueError as e:
            self.logger.log_error(e)

        self.last_row = self.__data.shape[0]
        self.index_row = 0

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
        self.current_closes = {ticker: price for ticker, price in zip(self.tickers, self.close[-1])}
        self.events.put(MarketEvent())
        return True
