
# from strategyrunner.data import DataManager, HistoricalDataHandler
# from strategyrunner.strategy import MomentumStrategy, BuyAndHold
# from strategyrunner.execution import SimulatedExecutionHandler
# from strategyrunner import Trader, Portfolio
# import time

# # bt = Trader(MomentumStrategy, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
# bt = Trader(BuyAndHold, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
# # bt.set_tickers(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV"])
# bt.set_tickers(['VFINX'])
# bt.set_dates("1988-08-01", "2012-12-31")
# bt.set_capital(10000)
# start = time.clock()
# bt._run()
# print("total: ", time.clock() - start, "s\n")


# with DataManager("data/test.db") as dm:
#     # data = dm.get_data(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV", "IGSB"], "2016-01-01", "2017-02-28")
#     data = dm.get_data(["AAPL"], "1988-08-01", "2018-10-01")
#
# print(data.head())

import zmq
import zmq.asyncio as zmqa
import asyncio
import json


async def server():
    socket = zmqa.Context().socket(zmq.PUB)
    socket.bind(f'tcp://127.0.0.1:4002')

    while True:
        await socket.send_multipart([b'A', b'', json.dumps({'a': 1}).encode()])
        await socket.send_multipart([b'B', b'', json.dumps({'b': 1}).encode()])
        await socket.send_multipart([b'C', b'', json.dumps({'c': 1}).encode()])
        print('sent')
        await asyncio.sleep(1)


async def client():
    socket = zmqa.Context().socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, [b'A', b'B'])
    # socket.setsockopt(zmq.SUBSCRIBE, b'B')
    socket.connect(f'tcp://127.0.0.1:4002')

    while True:
        [topic, _, msg] = await socket.recv_multipart()
        msg = json.loads(msg.decode())
        print(msg)


asyncio.ensure_future(server())
asyncio.ensure_future(client())
asyncio.get_event_loop().run_forever()