
from enum import Enum
from . import const
from .helpers import Signal


class Direction(Enum):
    BUY = 1
    SELL = 2


class Event:
    def __init__(self, event_type):
        self.type = event_type

    # def __repr__(self):
    #     return self.__str__()


class AccountOpenEvent(Event):
    def __init__(self, timestamp, sid, capital, broker, tickers, start_time=None, end_time=None):
        super(AccountOpenEvent, self).__init__(const.Event.ACCT_OPEN)
        self.timestamp = timestamp
        self.sid = sid
        self.capital = capital
        self.data_request = DataRequestEvent(broker, tickers, start_time, end_time)

    def __str__(self):
        return f'Account Open at {self.timestamp} for {self.sid} with capital {self.capital} and {self.data_request}'


class AccountCloseEvent(Event):
    def __init__(self, timestamp, sid):
        super(AccountCloseEvent, self).__init__(const.Event.ACCT_CLOSE)
        self.timestamp = timestamp
        self.sid = sid

    def __str__(self):
        return f'Account Close at {self.timestamp} for {self.sid}'


class DataRequestEvent(Event):
    def __init__(self, broker, tickers, start_time=None, end_time=None):
        super(DataRequestEvent, self).__init__(const.Event.DATA)
        if broker == const.Broker.SIMULATED and (start_time is None or end_time is None):
            raise ValueError('Time needed for simulated data request')

        self.broker = broker
        self.tickers = tickers
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        prefix = f'Data request from {self.broker} for {self.tickers}'
        if self.broker == const.Broker.SIMULATED:
            return prefix + f' from {self.start_time} to {self.end_time}'
        return prefix


class SignalEvent(Event):
    def __init__(self, timestamp, sid, signal: Signal):
        super(SignalEvent, self).__init__(const.Event.SIGNAL)
        self.timestamp = timestamp
        self.sid = sid
        self.signal = signal

    def __str__(self):
        text = "Signal event: "
        for k, v in self.signal.signal.items():
            text += f"{k}-> {v}\n"
        return text


class OrderEvent(Event):
    def __init__(self, sid, ticker, order_type, quantity):
        if quantity == 0:
            raise ValueError("Quantity is 0")

        super().__init__(const.Event.ORDER)
        self.sid = sid
        self.ticker = ticker
        self.order_type = order_type
        self.direction = Direction.BUY if quantity > 0 else Direction.SELL  # this is only used in print out
        self.quantity = quantity

    def __str__(self):
        return f"{self.direction.name} {abs(self.quantity): d} {self.ticker}"


class FillEvent(Event):
    def __init__(self, timestamp, sid, ticker, exchange, quantity, price, commission=0):
        super().__init__(const.Event.FILL)
        self.timestamp = timestamp
        self.sid = sid
        self.ticker = ticker
        self.exchange = exchange
        self.quantity = quantity
        self.price = price
        self.commission = commission

    def __str__(self):
        return f'Filled {self.quantity} {self.ticker} for strategy {self.sid} at {self.timestamp}'


class QuoteEvent(Event):
    def __init__(self, timestamp, sid, quotes: dict):
        super(QuoteEvent, self).__init__(const.Event.QUOTE)
        self.timestamp = timestamp
        self.sid = sid
        self.quotes = quotes

    def __str__(self):
        return f'Quotes at {self.timestamp} for {self.sid}: {self.quotes}'
