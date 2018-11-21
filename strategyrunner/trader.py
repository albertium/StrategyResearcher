
import queue
import zmq
import pandas as pd
from typing import Type

from .strategy import Strategy
from .logging import Logger
from .data import DataObject, HistoricalDataObject
from . import message
from . import const
from . import utils
from .helpers import Signal


class Trader:
    def __init__(self, strategy_class: Type[Strategy], config_file=None):

        self.data_obj = None  # type: DataObject
        self.strategy_class = strategy_class

        self.logger = Logger()
        self.orders_to_submit = queue.Queue()
        self.tickers = None
        self.start_time = None
        self.end_time = None
        self.initial_capital = None
        self.broker = None
        self.strategy = None

        self.strategy_name = strategy_class.name + '-' + utils.get_name_hash()
        print(f'Executing strategy {self.strategy_name}')

        config = utils.load_config(config_file)
        self.socket = zmq.Context().socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.strategy_name.encode())
        self.socket.connect(f'tcp://127.0.0.1:{config["manager_request_port"]}')

        self.order_socket = zmq.Context().socket(zmq.DEALER)
        self.order_socket.setsockopt(zmq.IDENTITY, self.strategy_name.encode())
        self.order_socket.connect(f'tcp://127.0.0.1:{config["manager_order_port"]}')

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

        self._set_data_obj()
        self.strategy = self.strategy_class(self.logger, self.data_obj)
        self.data_obj.set_look_back(self.strategy.look_back)

        signal = Signal(self.data_obj.tickers)
        while self.data_obj.update_bar():
            signal.reset()  # set all alphas to 0
            self.strategy.set_signal(signal)
            self.order_socket.send_json(message.gen_order_msg(self.data_obj.now, self.strategy_name, signal))

        # self.logger.close()

        self.socket.send_json(message.gen_acct_finish_msg('2017-12-31', self.strategy_name))

    def _set_data_obj(self):
        if self.tickers is None:
            raise ValueError("Tickers are not set")

        if self.broker == const.Broker.SIMULATED:
            if self.start_time is None:
                raise ValueError("Start time is not set")
            if self.end_time is None:
                raise ValueError("End time is not set")
            request = message.gen_data_request(self.broker.value, self.tickers, self.start_time, self.end_time)
        else:
            request = message.gen_data_request(self.broker.value, self.tickers)

        self.socket.send_json(message.gen_acct_create_msg(self.start_time, self.strategy_name, 10000, request))
        self.data_obj = self.socket.recv_pyobj().dispatch()

        if isinstance(self.data_obj, HistoricalDataObject):
            print(f'Historical data object received with {self.data_obj.last_row} data points')
        else:
            print('Data object received')
