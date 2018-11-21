
from ..strategy import Strategy
import numpy as np


class MomentumStrategy(Strategy):
    name = 'Momentum'

    def _setup(self):
        self.look_back = self.period = 120
        self.top = 3

    def set_signal(self, signal):
        returns = self.data.close[-1] / self.data.close[-self.period] - 1
        selected = np.argsort(returns) < self.top
        for ind, ticker in zip(selected, self.data.tickers):
            if ind > 0:
                signal[ticker] = int(ind)
