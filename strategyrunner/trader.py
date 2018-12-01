
import queue
import zmq
import pandas as pd
from typing import Type
import time

from .strategy import Strategy
from .logger import Logger
from .data import DataObject
from .event import AccountOpenEvent, AccountCloseEvent, SignalEvent
from .portfolio.trade_record import TradeRecord
from . import const
from . import utils
from .helpers import Signal


class Trader:
    def __init__(self, strategy_class: Type[Strategy], verbose=False, config_file=None):
        self.logger = Logger(strategy_class.name)
        self.verbose = verbose

        self.data_obj = None  # type: DataObject
        self.strategy_class = strategy_class

        self.orders_to_submit = queue.Queue()
        self.tickers = None
        self.start_time = None
        self.end_time = None
        self.initial_capital = None
        self.broker = None
        self.strategy = None

        self.strategy_name = strategy_class.name + '-' + utils.get_name_hash()
        self.logger.log_info(f'Executing strategy {self.strategy_name}')

        config = utils.load_config(config_file)
        self.socket = zmq.Context().socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.strategy_name.encode())
        self.socket.connect(f'tcp://127.0.0.1:{config["manager_request_port"]}')

    def set_tickers(self, tickers):
        self.tickers = tickers

    def set_time(self, start_date, end_date):
        self.start_time = pd.Timestamp(start_date)
        self.end_time = pd.Timestamp(end_date)

    def set_capital(self, initial_capital):
        self.initial_capital = initial_capital

    def set_broker(self, broker: const.Broker):
        self.broker = broker

    def trade(self):
        # check if necessary vales are set
        if self.initial_capital is None:
            raise ValueError("Initial capital is not set")
        if self.broker is None:
            raise ValueError("Broker is not set")

        wall_time_start = time.time()

        self._set_data_obj()
        self.strategy = self.strategy_class(self.logger, self.data_obj)
        self.data_obj.set_look_back(self.strategy.look_back)

        # main signal generation loop
        signal = Signal(self.data_obj.tickers)
        while self.data_obj.update_bar():
            signal.reset()  # set all alphas to 0
            self.strategy.set_signal(signal)
            signal_event = SignalEvent(self.data_obj.now, self.strategy_name, signal)
            self.socket.send_pyobj(signal_event)
            if self.verbose:
                self.logger.log_info(signal_event)

        wall_time_end = time.time()
        self.logger.log_info(f'Wall time: {wall_time_end - wall_time_start: .2f}s')

        if self.end_time is None:  # real-time
            self.socket.send_pyobj(AccountCloseEvent(pd.Timestamp.now(), self.strategy_name))
        else:
            self.socket.send_pyobj(AccountCloseEvent(self.end_time, self.strategy_name))

        result = self.socket.recv_pyobj()  # type: TradeRecord
        self.logger.log_info(f'Final capital: {result.get_equity()}')
        self.logger.log_info(f'Book-keeping time: {time.time() - wall_time_end: .2f}s')

        self.logger.close()

    def _set_data_obj(self):
        if self.tickers is None:
            raise ValueError("Tickers are not set")

        event = AccountOpenEvent(self.start_time, self.strategy_name, 10000, self.broker, self.tickers,
                                 self.start_time, self.end_time)

        self.logger.log_info(f'Requesting data: {event.data_request}')
        self.socket.send_pyobj(event)
        self.data_obj = self.socket.recv_pyobj().dispatch()  # type: DataObject

        if self.data_obj.type == const.Data.SIMULATED:
            self.logger.log_info(f'Historical data object received with {self.data_obj.last_row} data points')
        else:
            self.logger.log_info('Data object received')
