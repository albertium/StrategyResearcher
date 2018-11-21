
import pandas as pd
from .helpers import Signal
from . import const


def time_to_long(timestamp):
    return pd.Timestamp(timestamp).value


def gen_acct_create_msg(timestamp, sid, capital, data_request):
    return {'type': 'C', 'time': time_to_long(timestamp), 'sid': sid, 'cap': capital, 'data': data_request}


def parse_acct_create_msg(msg):
    return pd.Timestamp(msg['time']), msg['sid'], msg['cap'], parse_data_request(msg['data'])


def gen_acct_finish_msg(timestamp, sid):
    return {'type': 'F', 'time': time_to_long(timestamp), 'sid': sid}


def parse_acct_finish_msg(msg):
    return [pd.Timestamp(msg['time']), msg['sid']]


def gen_data_request(source, tickers, start_time, end_time):
    return {'src': source, 'tickers': tickers, 'start': time_to_long(start_time), 'end': time_to_long(end_time)}


def parse_data_request(msg):
    return const.Broker(msg['src']), msg['tickers'], pd.Timestamp(msg['start']), pd.Timestamp(msg['end'])


def gen_order_msg(timestamp, sid, signal: Signal):
    return {'time': time_to_long(timestamp), 'sid': sid, 'sig': signal.signal}


def parse_order_msg(msg):
    return pd.Timestamp(msg['time']), msg['sid'], msg['sig']
