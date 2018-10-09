
from strategytester.strategy.strategy import Strategy
from strategytester.data import DataHandler
import numpy as np


class MomentumStrategy(Strategy):
    def __init__(self, data: DataHandler):
        self.data = data
        self.period = 120
        self.top = 3

    def calculate_signal(self, signal):
        rets = self.data.close.iloc[-1] / self.data.close.iloc[-self.period] - 1
        selected = np.argsort(rets) < self.top
        for k in signal.keys():
            signal[k] = int(selected[k])
        return signal
