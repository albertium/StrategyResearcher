
from .execution import ExecutionHandler
from ..event import FillEvent, OrderEvent
from ..data import DataHandler
from queue import Queue


class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, data: DataHandler, events: Queue):
        self.data = data
        self.events = events

    def execute_order(self, event: OrderEvent):
        fill = FillEvent(self.data.now(), event.strategy_id, event.ticker, "SIM", event.quantity,
                         self.data.get_close(event.ticker))
        self.events.put(fill)
