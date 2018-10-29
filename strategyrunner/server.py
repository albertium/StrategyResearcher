
import asyncio
import zmq
import zmq.asyncio as zmqa
import concurrent.futures
import functools


class Server:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
    pool = []

    @classmethod
    def service(cls, socket_type, port):
        def decorator(func):
            def wrapper(self):
                socket = zmq.Context().socket(socket_type)
                socket.bind(f'tcp://127.0.0.1:{port}')
                while True:
                    func(self, socket)

            async def async_wrapper(self):
                socket = zmqa.Context().socket(socket_type)
                socket.bind(f'tcp://127.0.0.1:{port}')
                while True:
                    await func(self, socket)

            # if a regular function, need to schedule using thread
            if not asyncio.iscoroutinefunction(func):
                loop = asyncio.get_event_loop()

                async def task(self):
                    await loop.run_in_executor(cls.executor, wrapper, self)

                cls.pool.append(task)
                return task

            cls.pool.append(async_wrapper)
            return async_wrapper
        return decorator

    def job(self, func):
        pass

    def run(self):
        asyncio.get_event_loop().run_until_complete(asyncio.wait([func(self) for func in Server.pool]))
