
import queue
import zmq
import pandas as pd
from typing import Type

from .execution import ExecutionHandler
from .strategy import Strategy
from .logging import Logger
from .data import HistoricalDataRequest, DataObject


class Trader:
    def __init__(self, strategy_class: Type[Strategy], port=4002):

        self.data_obj = None  # type: DataObject
        self.strategy_class = strategy_class

        self.logger = Logger()
        self.orders_to_submit = queue.Queue()
        self.tickers = None
        self.start_date = None
        self.end_date = None
        self.initial_capital = None

        self.socket = zmq.Context().socket(zmq.DEALER)
        self.socket.connect(f'tcp://127.0.0.1:{port}')

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
        # check if necessary vales are set
        if self.initial_capital is None:
            raise ValueError("Initial capital is not set")

        # main run
        self._initialize_trading_instance()

        while self.data_obj.update_bar():
            signal = self.strategy.calculate_signal(self.data_obj)
            self.socket.send_json({'timestamp': self.data_obj.now, 'id': 1, 'sig': signal})

        self.logger.close()

    def _initialize_trading_instance(self):
        self._set_data_obj()
        self.strategy = self.strategy_class(self.logger, self.events, self.data_obj)

    def _set_data_obj(self):
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


