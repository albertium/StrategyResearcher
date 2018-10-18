
from ..strategy import Strategy
from ..data import DataHandler
from queue import Queue


class BuyAndHold(Strategy):
    def __init__(self, events: Queue, data: DataHandler):
        super().__init__(events, data)
        self.look_back = self.period = 1

    def _calculate_signal(self, signal):
        # equal weight on each ticker presented
        for ticker in signal.tickers:
            signal[ticker] = 1
        return signal
