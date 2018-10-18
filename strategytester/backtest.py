
import queue
import pandas as pd
from .event import EventType, SignalEvent
from .data import DataHandler
from .execution import ExecutionHandler
from .strategy import Strategy
from .portfolio import Portfolio
from typing import Type, List


class BackTest:
    def __init__(self,
                 strategy_class:          Type[Strategy],
                 portfolio_class:           Type[Portfolio],
                 data_handler_class:        Type[DataHandler],
                 execution_handler_class:   Type[ExecutionHandler]):

        self.strategy_class = strategy_class
        self.portfolio_class = portfolio_class
        self.data_handler_class = data_handler_class
        self.execution_handler_class = execution_handler_class

        self.events = queue.Queue()
        self.tickers = None
        self.start_date = None
        self.end_date = None
        self.initial_capital = None

    def set_tickers(self, tickers):
        self.tickers = tickers

    def set_dates(self, start_date, end_date):
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)

    def set_capital(self, initial_capital):
        self.initial_capital = initial_capital

    def run(self):
        # check if necessary vales are set
        if self.tickers is None:
            raise ValueError("Tickers are not set")
        if self.start_date is None:
            raise ValueError("Start date is not set")
        if self.end_date is None:
            raise ValueError("End date is not set")
        if self.initial_capital is None:
            raise ValueError("Initial capital is not set")

        # main run
        self._initialize_trading_instance()
        while self.data_handler.update_bar():
            while True:
                try:
                    event = self.events.get(block=False)
                except queue.Empty:
                    break

                if event.type == EventType.MARKET:
                    signal = SignalEvent(1, self.tickers)
                    self.strategy.calculate_signal(signal)
                    self.portfolio.take_snapshot()
                elif event.type == EventType.SIGNAL:
                    self.portfolio.submit_order(event)
                elif event.type == EventType.ORDER:
                    self.execution_handler.execute_order(event)
                elif event.type == EventType.FILL:
                    self.portfolio.handle_fill(event)

        result = self.portfolio.get_history(1)
        print(result)

    def _initialize_trading_instance(self):
        self.data_handler = self.data_handler_class(self.events, self.tickers, self.start_date, self.end_date)
        self.strategy = self.strategy_class(self.events, self.data_handler)
        self.portfolio = self.portfolio_class(self.data_handler, self.events, self.initial_capital)
        self.execution_handler = self.execution_handler_class(self.data_handler, self.events)

