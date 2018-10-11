
from abc import ABC, abstractmethod
from ..data import DataHandler
from ..event import SignalEvent
from queue import Queue


class Strategy(ABC):
    def __init__(self, events: Queue, data: DataHandler):
        self.data = data
        self.events = events
        self.look_back = -1

    def calculate_signal(self, signal: SignalEvent):
        if 0 < self.look_back <= len(self.data.close):
            self.events.put(self._calculate_signal(signal))

    @abstractmethod
    def _calculate_signal(self, signal: SignalEvent):
        raise NotImplementedError("calculate_signal is not implemented")
