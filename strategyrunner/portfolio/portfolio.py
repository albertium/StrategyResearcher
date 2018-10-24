
from strategyrunner.event import OrderEvent
from ..execution import OrderType
from .trade_record import TradeRecord
from ..event import SignalEvent,FillEvent
from ..data import DataHandler
from ..logging import Logger
from queue import Queue


class Portfolio:
    def __init__(self, logger: Logger, data: DataHandler, events: Queue, start_date, initial_capital=10000):
        self.logger = logger
        self.data = data
        self.events = events
        self.start_date = start_date
        self.initial_capital = initial_capital
        self.positions = {}

    def submit_order(self, signal_event: SignalEvent):
        sid = signal_event.strategy_id
        if sid not in self.positions:
            self.positions[sid] = TradeRecord(self.data.now(), self.initial_capital, signal_event.tickers)
        positions = self.positions[sid]

        # equal weight sizing
        fund_per_alpha = positions.get_equity() / sum([abs(x) for x in signal_event.signals.values()])

        # TODO: this assumes order will be fully filled. Partially filled hanging order need to be dealt with later
        # TODO: also, quantity may cause overflow if not instantly filled
        orders = []
        for ticker, alpha in signal_event.signals.items():
            pos = int(alpha * fund_per_alpha / self.data.get_close(ticker))
            delta = pos - positions[ticker]
            if delta != 0:
                orders.append([delta, pos, ticker])

        orders = sorted(orders)
        for [quantity, pos, ticker] in orders:
            order = OrderEvent(sid, ticker, OrderType.LMT, quantity)
            self.events.put(order)
            self.logger.log_info(f"{order} ({positions[ticker]} -> {pos})")

    def handle_fill(self, fill: FillEvent):
        self.logger.log_info(fill)
        self.positions[fill.strategy_id].update(fill.ticker, fill.quantity, fill.price, fill.commission)

    def take_snapshot(self):
        prices = self.data.get_closes()
        for position in self.positions.values():
            position.take_snapshot(self.data.now(), prices)
            self.logger.log_info(f"\n{position}\n")

    def get_history(self, strategy_id) -> TradeRecord:
        return self.positions[strategy_id]
