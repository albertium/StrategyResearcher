

class Signal:
    def __init__(self, tickers):
        self.tickers = tickers
        self.template = {ticker: 0 for ticker in self.tickers}
        self.signal = None  # type: dict
        self.reset()

    def __setitem__(self, key, value):
        if key not in self.signal:
            raise ValueError(f'Ticker {key} is not available for the current trader')
        self.signal[key] = value

    def values(self):
        if self.signal is None:
            raise RuntimeError('Signal is not set yet')
        return self.signal.values()

    def items(self):
        if self.signal is None:
            raise RuntimeError('Signal is not set yet')
        return self.signal.items()

    def reset(self):
        self.signal = self.template.copy()

    def __str__(self):
        return str(self.signal)

    def __repr__(self):
        return self.__str__()