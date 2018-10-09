
from abc import ABC, abstractmethod
import pandas as pd


class DataHandler(ABC):
    def __init__(self):
        self.open = None
        self.high = None
        self.low = None
        self.close = None  # type: pd.DataFrame

    @abstractmethod
    def update_bar(self):
        raise NotImplementedError("update_bar is not implemented")

    def get_close(self, ticker):
        return self.close.iloc[-1][ticker]

    def now(self):
        return self.close.last_valid_index()
