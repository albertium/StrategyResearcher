
import asyncio
import zmq
import zmq.asyncio as zmqa
import concurrent.futures
import functools
from abc import ABC, abstractmethod
from enum import Enum


class ServiceType(Enum):
    Server = 1
    Client = 2


class Service(ABC):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    @classmethod
    def service(cls, agent_type, socket_type, ports):
        if agent_type == ServiceType.Server:
            if socket_type not in [zmq.REP, zmq.PUB]:
                raise ValueError('Invalid socket type for server')
        elif agent_type == ServiceType.Client:
            if socket_type not in [zmq.REQ, zmq.SUB]:
                raise ValueError('Invalid socket type for client')
        else:
            raise ValueError('Invalid agent type')

        if not isinstance(ports, list):
            ports = [ports]

        def decorator(func):
            if not asyncio.iscoroutinefunction(func):
                raise ValueError('Function should be async')

            jobs = []
            for port in ports:
                async def wrapper(self):
                    try:
                        socket = zmqa.Context().socket(socket_type)
                        if agent_type == ServiceType.Server:
                            socket.bind(f'tcp://127.0.0.1:{port}')
                        else:
                            socket.connect(f'tcp://127.0.0.1:{port}')

                        while True:
                            await func(self, socket)

                    except (asyncio.CancelledError, KeyboardInterrupt):
                        print(f'Port {port} shutdown')
                    except Exception as e:
                        print(f'Port {port} exception: {e}')

                jobs.append(wrapper)

            async def aggregator(self):
                await asyncio.wait([job(self) for job in jobs])

            return aggregator
        return decorator

    @classmethod
    def job(cls, func):
        if asyncio.iscoroutinefunction(func):
            raise ValueError('Function should NOT be async')

        loop = asyncio.get_event_loop()

        async def wrapper(self, *args, **kwargs):
            return await loop.run_in_executor(cls.executor, functools.partial(func, self, *args, **kwargs))

        return wrapper

    @abstractmethod
    def _run(self) -> list:
        pass

    def run(self):
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(*self._run())
        try:
            print('Service started')
            loop.run_until_complete(tasks)
        except KeyboardInterrupt:
            print(f'Interrupted')
            for task in asyncio.Task.all_tasks():
                task.cancel()
            loop.stop()
            loop.run_forever()
            print(tasks.done())
            # tasks.exception()
        finally:
            loop.close()
