
from strategytester.event import OrderEvent
from ..execution import OrderType
from .trade_record import TradeRecord
from ..event import FillEvent
from ..data import DataHandler
from queue import Queue


class Portfolio:
    def __init__(self, data: DataHandler, events: Queue, start_date, initial_capital=10000):
        self.data = data
        self.events = events
        self.start_date = start_date
        self.initial_capital = initial_capital
        self.positions = {}

    def submit_order(self, signal_event):
        sid, signal = signal_event.strategy_id, signal_event.signal
        if sid not in self.positions:
            self.positions[sid] = TradeRecord(self.initial_capital, signal.keys())
        positions = self.positions[sid]

        # equal weight sizing
        multiplier = positions.get_total_holding() / sum([abs(x) for x in signal_event.signal.values()])

        # TODO: this assumes order will be fully filled. Partially filled hanging order need to be dealt with later
        # TODO: also, quantity may cause overflow if not instantly filled
        for ticker, alpha in signal_event.signal.iteritem():
            pos = int(alpha * multiplier)  # Note that using floor here makes short position overstated
            order = OrderEvent(sid, ticker, OrderType.LMT, pos - positions[ticker])
            self.events.put(order)
            print(f"{order} ({positions[ticker]} -> {pos}", flush=True)

    def handle_fill(self, fill: FillEvent):
        self.positions[fill.strategy_id].update(fill.ticker, fill.quantity, fill.price, fill.commission)

    def take_snapshot(self, strategy_id):
        self.positions[strategy_id].take_snapshot(self.data.close.index[-1], self.data.close.iloc[-1, :])
