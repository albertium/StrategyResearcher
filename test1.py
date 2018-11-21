

import zmq
from enum import Enum
import pickle
import json
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


def parse_msg(msg):
    return pd.Timestamp(msg['start']), pd.Timestamp(msg['end']), Source(msg['src']), msg['tickers']


socket = zmq.Context().socket(zmq.ROUTER)
socket.bind('tcp://127.0.0.1:5000')

print('started')

while True:
    pid, _, msg = socket.recv_multipart()
    _ = pickle.loads(msg)
    # _ = parse_msg(json.loads(msg.decode()))
    socket.send_multipart([pid, b'', b'reply'])
