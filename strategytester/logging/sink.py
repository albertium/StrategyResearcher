
from enum import Enum
from .log import Log, Level
import sys


class SinkLevel(Enum):
    CRITICAL = 1
    INFO = 2
    ALL = 3


class Sink:
    def __init__(self, level: SinkLevel, out='stdout'):
        self.level = level
        self.out = out
        if out == 'stdout':
            self.stream = sys.stdout
        else:
            self.stream = open(out, 'w')

    def dump(self, log: Log):
        if self.level == SinkLevel.ALL \
                or (self.level == SinkLevel.CRITICAL and log.level != Level.INFO) \
                or (self.level == SinkLevel.INFO and log.level == Level.INFO):
            print(log, file=self.stream, flush=True)

    def close(self):
        if self.out != 'stdout':
            self.stream.close()
