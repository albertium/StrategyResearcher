
import asyncio
import signal
from abc import ABC, abstractmethod
import traceback
import threading


class AsyncAgent(ABC):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.futures = None
        self.events = []

    @abstractmethod
    def _run(self):
        raise NotImplementedError

    async def await_coroutine(self, coro, msg=''):
        if msg:
            print(msg)

        while True:
            try:
                await coro()
            except Exception as e:
                print('Caught exceptions:')
                traceback.print_exc()

    @staticmethod
    async def exception_wrapper(coro):
        try:
            await coro
        except Exception as e:
            print('Caught exceptions:')
            traceback.print_exc()

    def submit_task(self, coro):
        asyncio.ensure_future(self.exception_wrapper(coro))

    @staticmethod
    def run_task(coro):
        asyncio.new_event_loop().run_until_complete(AsyncAgent.exception_wrapper(coro))

    async def shutdown(self):
        print('Shutting down agent')

        # set all the threading.Event to true so that the outside loop can finish
        for event in self.events:
            event.set()

        for task in asyncio.Task.all_tasks():
            if task is not asyncio.Task.current_task():
                task.cancel()
        self.loop.stop()

    def run(self, signals=None):
        if signals is None:
            signals = [signal.SIGINT]

        for sig in signals:
            self.loop.add_signal_handler(sig, lambda s=sig: asyncio.ensure_future(self.shutdown()))

        try:
            self.futures = [asyncio.ensure_future(self.await_coroutine(coro, msg)) for coro, msg in self._run()]
            self.loop.run_forever()
        finally:
            print(f'Agent shut down')
            self.loop.stop()

    def run_in_fork(self, signals=None):
        if signals is None:
            signals = [signal.SIGINT]

        for sig in signals:
            self.loop.add_signal_handler(sig, lambda s=sig: asyncio.run_coroutine_threadsafe(self.shutdown(), self.loop))

        self.futures = [asyncio.run_coroutine_threadsafe(self.await_coroutine(coro, msg), self.loop)
                        for coro, msg in self._run()]
        threading.Thread(target=self.loop.run_forever).start()
