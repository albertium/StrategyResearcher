
from strategytester.strategy.strategy import Strategy
from strategytester.data import DataHandler
import numpy as np
from queue import Queue


class MomentumStrategy(Strategy):
    def __init__(self, events: Queue, data: DataHandler):
        super().__init__(events, data)
        self.look_back = self.period = 120
        self.top = 3

    def _calculate_signal(self, signal):
        returns = self.data.close.iloc[-1] / self.data.close.iloc[-self.period] - 1
        selected = np.argsort(returns) < self.top
        for ticker in signal.tickers:
            signal[ticker] = int(selected[ticker])
        return signal

