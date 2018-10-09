
from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def calculate_signal(self, signal):
        raise NotImplementedError("calculate_signal is not implemented")
