
from abc import ABC, abstractmethod
from ..data import DataHandler
from ..event import SignalEvent
from ..logging import Logger
from queue import Queue


class Strategy(ABC):
    def __init__(self, logger: Logger, events: Queue, data: DataHandler):
        self.logger = logger
        self.data = data
        self.events = events
        self.look_back = -1
        self._setup()  # for user initializationt

    def calculate_signal(self, signal: SignalEvent):
        if self.look_back < 0 or len(self.data.close) >= self.look_back:
            self.events.put(self._calculate_signal(signal))

    @abstractmethod
    def _setup(self):
        pass

    @abstractmethod
    def _calculate_signal(self, signal: SignalEvent):
        raise NotImplementedError("calculate_signal is not implemented")
