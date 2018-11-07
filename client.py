
import zmq
from concurrent import futures
from strategyrunner.data import HistoricalDataRequest


def request(cid):
    socket = zmq.Context().socket(zmq.REQ)
    socket.setsockopt(zmq.IDENTITY, str(cid).encode())
    socket.connect('tcp://127.0.0.1:4000')

    print(f'client {cid} ready')
    socket.send_pyobj(HistoricalDataRequest(['AAPL'], '2014-01-01', '2018-07-30'))
    print(f'client {cid} request sent')
    msg = socket.recv_pyobj()
    print(f'client {cid} received data object {msg.last_row}')


pool = futures.ThreadPoolExecutor(max_workers=10)
print('start requesting')
pool.map(request, range(10))