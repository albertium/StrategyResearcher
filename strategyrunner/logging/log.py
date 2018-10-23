
from enum import Enum


class Level(Enum):
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    INFO = 'INFO'


class Log:
    def __init__(self, timestamp, level, msg):
        self.timestamp = timestamp
        self.level = level
        self.msg = msg

    def __str__(self):
        return f'{self.timestamp} [{self.level.value}] {self.msg}'

    def __repr__(self):
        return self.__str__()

    def is_critical(self):
        return self.level != Level.INFO
