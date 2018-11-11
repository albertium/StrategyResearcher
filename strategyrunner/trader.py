
import queue
import zmq
import pandas as pd
from typing import Type

from .event import EventType, SignalEvent
from .execution import ExecutionHandler
from .strategy import Strategy
from .portfolio import Portfolio
from .logging import Logger
from .data import HistoricalDataRequest, DataObject

class Trader:
    def __init__(self,
                 strategy_class:            Type[Strategy],
                 portfolio_class:           Type[Portfolio],
                 execution_handler_class:   Type[ExecutionHandler]):

        self.data_obj = None  # type: DataObject
        self.strategy_class = strategy_class
        self.portfolio_class = portfolio_class
        self.execution_handler_class = execution_handler_class

        self.logger = Logger()
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

    def simulated_trade(self):
        pass

    def live_trade(self):
        pass

    def _run(self):
        tmp = 0
        # check if necessary vales are set
        if self.initial_capital is None:
            raise ValueError("Initial capital is not set")

        # main run
        self._initialize_trading_instance()

        while self.data_obj.update_bar():
            signal = SignalEvent(1, self.tickers)
            self.strategy.calculate_signal(signal)
            self.portfolio.take_snapshot()

        result = self.portfolio.get_history(1)
        print(f'Sharpe Ratio: {result.get_sharpe_ratio()}')
        self.logger.close()

    def _initialize_trading_instance(self):
        self.request_data_obj()
        self.strategy = self.strategy_class(self.logger, self.events, self.data_handler)

    def request_data_obj(self):
        if self.tickers is None:
            raise ValueError("Tickers are not set")
        if self.start_date is None:
            raise ValueError("Start date is not set")
        if self.end_date is None:
            raise ValueError("End date is not set")

        socket = zmq.Context().socket(zmq.REQ)
        # socket.setsockopt(zmq.IDENTITY, str(cid).encode())
        socket.connect('tcp://127.0.0.1:4000')

        socket.send_pyobj(HistoricalDataRequest(self.tickers, self.start_date, self.end_date))
        self.data_obj = socket.recv_pyobj().dispatch()
