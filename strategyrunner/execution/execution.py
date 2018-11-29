
from enum import Enum
from abc import ABC, abstractmethod
from ..data import DataHandler
from ..logging import Logger
from queue import Queue





class ExecutionHandler(ABC):
    def __init__(self, logger: Logger, data: DataHandler, events: Queue):
        self.logger = logger
        self.data = data
        self.events = events

    @abstractmethod
    def execute_order(self, event):
        pass
