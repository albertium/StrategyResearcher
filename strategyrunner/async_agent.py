
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

    @staticmethod
    async def coroutine_wrapper(coro, *args):
        alive = True
        while alive is True:
            try:
                alive = await coro(*args)
            except Exception as e:
                print('Caught exceptions:')
                traceback.print_exc()

    def run_coroutine(self, msg, coro, *args):
        if msg:
            print(msg)
        return asyncio.ensure_future(self.coroutine_wrapper(coro, *args))

    def run_coroutine_threadsafe(self, msg, coro, *args):
        if msg:
            print(msg)
        return asyncio.run_coroutine_threadsafe(self.coroutine_wrapper(coro, *args), self.loop)

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
            self.loop.run_forever()
        finally:
            print(f'Agent shut down')
            self.loop.stop()

    def run_in_fork(self, signals=None):
        if signals is None:
            signals = [signal.SIGINT]

        for sig in signals:
            self.loop.add_signal_handler(sig, lambda s=sig: asyncio.run_coroutine_threadsafe(self.shutdown(), self.loop))

        thread = threading.Thread(target=self.loop.run_forever)
        thread.start()
        return thread
