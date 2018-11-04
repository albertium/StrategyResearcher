
from strategyrunner.service import Service, ServiceType


import time
import zmq


class A(Service):
    @Service.service(ServiceType.Server, zmq.REP, 5555)
    async def response(self, socket: zmq.Socket):
        msg = await socket.recv_json()
        print(type(msg['number']))
        await socket.send_json({'reply': 1})

    def _run(self):
        return [self.response]

a = A()
a.run()

# class A(Service):
#     @Service.service(ServiceType.Server, zmq.REP, 5555)
#     async def response(self, socket: zmq.Socket):
#         msg = await socket.recv_json()
#         print(type(msg['number']))
#         await socket.send_json({'reply': 1})
#
# a = A()
# a.run()