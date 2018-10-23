
from .execution import ExecutionHandler
from ..event import FillEvent, OrderEvent
from ..data import DataHandler
from ..logging import Logger
from queue import Queue


class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, logger: Logger, data: DataHandler, events: Queue):
        super().__init__(logger, data, events)

    def execute_order(self, event: OrderEvent):
        fill = FillEvent(self.data.now(), event.strategy_id, event.ticker, "SIM", event.quantity,
                         self.data.get_close(event.ticker))
        self.events.put(fill)
