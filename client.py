
import zmq
from concurrent import futures
from strategyrunner.data import HistoricalDataRequest, RealTimeDataRequest, DataObject
import traceback


def request(cid):
    socket = zmq.Context().socket(zmq.REQ)
    socket.setsockopt(zmq.IDENTITY, str(cid).encode())
    socket.connect('tcp://127.0.0.1:4000')

    print(f'client {cid} ready')
    # socket.send_pyobj(HistoricalDataRequest(['AAPL'], '2014-01-01', '2018-07-30'))
    socket.send_pyobj(RealTimeDataRequest(['AAPL']))
    print(f'client {cid} request sent')
    msg = socket.recv_pyobj()
    print(msg)
    data_obj = msg.dispatch()  # type: DataObject

    print('are we here?')
    while data_obj.update_bar():
        print(data_obj.close)
        print(data_obj.low)
    print('what?')
    # print(f'client {cid} received data object {msg.last_row}')


pool = futures.ThreadPoolExecutor(max_workers=10)
print('start requesting')
futs = [pool.submit(request, cid) for cid in range(1)]

for fut in futures.as_completed(futs):
    try:
        print(fut.result())
    except Exception as e:
        print('Exception:')
        traceback.print_exc()

# request(1)