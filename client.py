

import zmq
import time
import asyncio


async def run_task(id, port):
    socket = zmq.Context().socket(zmq.REQ)
    socket.connect(f'tcp://127.0.0.1:{port}')

    while True:
        socket.send_string(f'{id} client msg')
        msg = socket.recv_string()
        print(f'client {id} get message {msg}')
        await asyncio.sleep(1)

asyncio.get_event_loop().run_until_complete(asyncio.wait([run_task(i, 5555) for i in [1, 2]]))
