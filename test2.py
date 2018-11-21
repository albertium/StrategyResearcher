
import zmq
from enum import Enum
import time
import pandas as pd


class Source(Enum):
    ALIVE = 1
    FINISH = 2


class Message:
    def __init__(self, start, end, source, tickers):
        self.start = start
        self.end = end
        self.source = source
        self.tickers = tickers


def gen_msg(start, end, src, tickers):
    return {'start': pd.Timestamp(start).value, 'end': pd.Timestamp(end).value, 'src': src.value, 'tickers': tickers}


socket = zmq.Context().socket(zmq.REQ)
socket.connect('tcp://127.0.0.1:5000')

tic = time.clock()

for _ in range(100000):
    msg = Message(pd.Timestamp(2017, 1, 1), pd.Timestamp(2018, 1, 1), Source.ALIVE, ['AAPL, GOOG'])
    # msg = gen_msg(pd.Timestamp(2017, 1, 1), pd.Timestamp(2018, 1, 1), Source.ALIVE, ['AAPL, GOOG'])
    socket.send_pyobj(msg)
    # socket.send_json(msg)
    reply = socket.recv_string()

print(f'Elapsed: {time.clock() - tic}s')
