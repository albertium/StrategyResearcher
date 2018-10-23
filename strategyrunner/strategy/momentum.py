
from ..strategy import Strategy
import numpy as np


class MomentumStrategy(Strategy):
    def _setup(self):
        self.look_back = self.period = 120
        self.top = 3

    def _calculate_signal(self, signal):
        returns = self.data.close.iloc[-1] / self.data.close.iloc[-self.period] - 1
        selected = np.argsort(returns) < self.top
        for ticker in signal.tickers:
            signal[ticker] = int(selected[ticker])
        return signal
