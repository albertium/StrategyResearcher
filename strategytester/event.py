
from enum import Enum


class EventType(Enum):
    MARKET = 1
    SIGNAL = 2
    ORDER = 3
    FILL = 4


class Direction(Enum):
    BUY = 1
    SELL = 2


class Event:
    def __init__(self, event_type):
        self.type = event_type


class MarketEvent(Event):
    def __init__(self):
        super().__init__(EventType.MARKET)


class SignalEvent(Event):
    def __init__(self, strategy_id, signals):
        super().__init__(EventType.SIGNAL)
        self.strategy_id = strategy_id
        self.signals = signals


class OrderEvent(Event):
    def __init__(self, strategy_id, ticker, order_type, quantity):
        if quantity == 0:
            raise ValueError("Quantity is 0")

        super().__init__(EventType.ORDER)
        self.strategy_id = strategy_id
        self.ticker = ticker
        self.order_type = order_type
        self.direction = Direction.BUY if quantity > 0 else Direction.SELL
        self.quantity = abs(quantity)

    def __str__(self):
        return f"{self.direction.name} {self.quantity:d} {self.ticker}"

    def __repr__(self):
        return self.__str__()


class FillEvent(Event):
    def __init__(self, timestamp, strategy_id, ticker, exchange, quantity, price, commission=0):
        super().__init__(EventType.FILL)
        self.timestamp = timestamp
        self.strategy_id = strategy_id
        self.ticker = ticker
        self.exchange = exchange
        self.quantity = quantity
        self.price = price
        self.commission = commission
