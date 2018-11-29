
from enum import Enum
from . import const
from .helpers import Signal


class Direction(Enum):
    BUY = 1
    SELL = 2


class Event:
    def __init__(self, event_type):
        self.type = event_type  # type: const.Event

    def __repr__(self):
        return self.__str__()


class BaseEvent(Event):
    def __init__(self, event_type, timestamp, sid):
        super(BaseEvent, self).__init__(event_type)
        self.timestamp = timestamp
        self.sid = sid

    def __str__(self):
        return f'[{self.timestamp}]|{self.sid}|{self.type.name}:'


class AccountOpenEvent(BaseEvent):
    def __init__(self, timestamp, sid, capital, broker, tickers, start_time=None, end_time=None, pid=None):
        super(AccountOpenEvent, self).__init__(const.Event.ACCT_OPEN, timestamp, sid)
        self.capital = capital
        self.data_request = DataRequestEvent(broker, tickers, start_time, end_time)
        self.pid = pid

    def __str__(self):
        text = super(AccountOpenEvent, self).__str__()
        return f'{text} capital -> {self.capital} / data -> {self.data_request.tickers}'


class AccountCloseEvent(BaseEvent):
    def __init__(self, timestamp, sid, pid=None):
        super(AccountCloseEvent, self).__init__(const.Event.ACCT_CLOSE, timestamp, sid)
        self.pid = pid

    def __str__(self):
        text = super(AccountCloseEvent, self).__str__()
        return f'{text} done'


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


class SignalEvent(BaseEvent):
    def __init__(self, timestamp, sid, signal: Signal):
        super(SignalEvent, self).__init__(const.Event.SIGNAL, timestamp, sid)
        self.signal = signal

    def __str__(self):
        text = super(SignalEvent, self).__str__() + '\n'
        text += '\n'.join([f'   {ticker} $ {sig}' for ticker, sig in self.signal.signal.items()]) + '\n'
        return text


class OrderEvent(BaseEvent):
    def __init__(self, timestamp, sid):
        super(OrderEvent, self).__init__(const.Event.ORDER, timestamp, sid)
        self.orders = {}

    def add(self, ticker, order_type, quantity):
        if quantity == 0:
            raise ValueError('Quantity shouldn''t be 0')
        self.orders[ticker] = [order_type, quantity]

    def added(self):
        return len(self.orders) > 0

    def __str__(self):
        text = super(OrderEvent, self).__str__() + '\n'
        text += '\n'.join([f'   {ticker} -> {qty: d}' for ticker, (_, qty) in self.orders.items()]) + '\n'
        return text


class FillEvent(BaseEvent):
    def __init__(self, timestamp, sid):
        super(FillEvent, self).__init__(const.Event.FILL, timestamp, sid)
        self.fills = {}

    def add(self, ticker, price, quantity, commission=0):
        self.fills[ticker] = [quantity, price, commission]

    def __str__(self):
        text = super(FillEvent, self).__str__() + '\n'
        text += '\n'.join([f'   {ticker} {qty: d} @ {price}' for ticker, (qty, price, com) in self.fills.items()]) + '\n'
        return text


class QuoteEvent(BaseEvent):
    def __init__(self, timestamp, sid, quotes: dict):
        super(QuoteEvent, self).__init__(const.Event.QUOTE, timestamp, sid)
        self.quotes = quotes

    def __str__(self):
        text = super(QuoteEvent, self).__str__() + '\n'
        text += '\n'.join([f'   {ticker} @ {price}' for ticker, price in self.quotes.items()]) + '\n'
        return text
