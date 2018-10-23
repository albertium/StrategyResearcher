
from ..strategy import Strategy


class BuyAndHold(Strategy):
    def _setup(self):
        self.look_back = 1

    def _calculate_signal(self, signal):
        # equal weight on each ticker presented
        for ticker in signal.tickers:
            signal[ticker] = 1
        return signal
