
from abc import ABC, abstractmethod
from ..data import DataObject
from ..logger import Logger
from ..helpers import Signal


class Strategy(ABC):
    name = "Base"

    def __init__(self, logger: Logger, data: DataObject):
        self.logger = logger
        self.data = data
        self.look_back = -1
        self._setup()  # for user initialization

    @abstractmethod
    def set_signal(self, signal: Signal) -> None:
        raise NotImplementedError('set_signal is not implemented')

    @abstractmethod
    def _setup(self):
        pass


class HyperParameter:
    counter = 0

    def __init__(self):
        self.order = HyperParameter.counter
        HyperParameter.counter += 1


class DiscreteHyperParameter(HyperParameter):
    def __init__(self, lb, ub, step):
        super().__init__()
        self.lb = lb
        self.ub = ub
        self.step = step


class ContinuousHyperParameter(HyperParameter):
    def __init__(self, lb, ub):
        super().__init__()
        self.lb = lb
        self.ub = ub
