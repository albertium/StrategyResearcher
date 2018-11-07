
import asyncio
import signal
from abc import ABC, abstractmethod
import traceback


class AsyncAgent(ABC):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.futures = None

    @abstractmethod
    def _run(self):
        raise NotImplementedError

    async def handle_exception(self, coro):
        try:
            await coro
        except Exception as e:
            print(f'Caught exceptions')
            traceback.print_exc()
            await self.shutdown()

    async def shutdown(self):
        print('Shutting down agent')
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
            self.futures = [asyncio.ensure_future(self.handle_exception(coro)) for coro in self._run()]
            self.loop.run_forever()
        finally:
            print(f'Agent shut down')
            self.loop.stop()
