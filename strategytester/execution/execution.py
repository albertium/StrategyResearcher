
from enum import Enum
from abc import ABC, abstractmethod


class OrderType(Enum):
    LMT = 1
    MKT = 2


class ExecutionHandler(ABC):
    @abstractmethod
    def execute_order(self, event):
        pass
