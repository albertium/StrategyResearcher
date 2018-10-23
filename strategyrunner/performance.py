
from .portfolio import TradeRecord
import numpy as np


class Performance:
    def __init__(self, record: TradeRecord):
        self.data = record.get_history()

    def get_sharpe_ratio(self):
        ret = self.data.pct_change()
        return ret.mean() / ret.std() * np.sqrt(252)  # assume daily returns

    def plot(self):
        self.data.plot()
