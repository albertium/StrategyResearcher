
from abc import ABC, abstractmethod
import pandas as pd
from queue import Queue
from typing import List


class DataHandler(ABC):
    def __init__(self, events: Queue, tickers: List, start_date, end_date):
        self.events = events
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date

        self.open = None
        self.high = None
        self.low = None
        self.close = None  # type: pd.DataFrame

    @abstractmethod
    def update_bar(self):
        raise NotImplementedError("update_bar is not implemented")

    def get_close(self, ticker):
        return self.close.iloc[-1][ticker]

    def get_closes(self):
        return self.close.iloc[-1, :]

    def now(self):
        return self.close.last_valid_index()
