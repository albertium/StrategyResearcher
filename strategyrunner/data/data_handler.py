
from abc import ABC, abstractmethod
from queue import Queue
from typing import List
from ..logging import Logger


class DataHandler(ABC):
    def __init__(self, logger: Logger, events: Queue, tickers: List, start_date, end_date):
        self.logger = logger
        self.events = events
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date

        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.current_closes = None
        self._now = None

    @abstractmethod
    def update_bar(self):
        raise NotImplementedError("update_bar is not implemented")

    def get_closes(self):
        return self.current_closes

    def get_close(self, ticker):
        return self.current_closes[ticker]

    def now(self):
        return self._now
