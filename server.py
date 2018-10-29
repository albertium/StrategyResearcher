
from strategyrunner.server import Server
import zmq


import time
import zmq
import zmq.asyncio as zmqa


# class A(Server):
#     @Server.service(zmq.REP, 5555)
#     def response(self, socket):
#         msg = socket.recv_string()
#         print(msg)
#         socket.send_string('received')
#
# a = A()
# a.run()

class A(Server):
    @Server.service(zmq.REP, 5555)
    async def response(self, socket):
        msg = await socket.recv_string()
        print(msg)
        await socket.send_string('received')

a = A()
a.run()


# import time
# import zmq
# import zmq.asyncio as zmqa
# import asyncio
#
# socket = zmqa.Context().socket(zmq.REP)
# socket.bind(f'tcp://127.0.0.1:{5555}')
#
#
# async def run():
#     while True:
#         msg = await socket.recv_string()
#         print(msg)
#         socket.send_string('received')
#         await asyncio.sleep(1)
#
#
# asyncio.get_event_loop().run_until_complete(asyncio.wait([run()]))
