
from enum import Enum


class Event(Enum):
    MARKET = 1
    SIGNAL = 2
    ORDER = 3
    FILL = 4
    QUOTE = 5
    ACCT_OPEN = 6
    ACCT_CLOSE = 7
    DATA = 8


class Data(Enum):
    SIMULATED = 1
    REALTIME = 2


class Broker(Enum):
    SIMULATED = 'H'
    INTERACTIVE_BROKERS = 'IB'  # IB


class Order(Enum):
    LMT = 1
    MKT = 2


class Log(Enum):
    ERROR = 1
    WARNING = 2
    INFO = 3
    CLOSE = 4


class Level(Enum):
    CRITICAL = 1
    INFO = 2
    ALL = 3