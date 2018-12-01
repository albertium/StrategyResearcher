
import asyncio
import queue
from pandas import Timestamp
from pathlib import Path
import time
import os
import sys

from . import const
from .async_agent import AsyncAgent
from .utils import get_name_hash


class Log:
    def __init__(self, timestamp, log_type: const.Log, msg):
        self.timestamp = timestamp
        self.type = log_type
        self.msg = msg

    def __str__(self):
        return f'{self.timestamp.strftime("%Y-%m-%d %H:%M:%S")} [{self.type.name}]>> {self.msg}'

    def __repr__(self):
        return self.__str__()

    def is_critical(self):
        return self.type != const.Log.INFO


class Sink:
    def __init__(self, level: const.Level, out='stdout'):
        self.level = level
        self.out = out
        if out == 'stdout':
            self.stream = sys.stdout
        else:
            self.stream = open(out, 'w')

    def dump(self, log: Log):
        if self.level == const.Level.ALL \
                or (self.level == const.Level.CRITICAL and log.type != const.Log.INFO) \
                or (self.level == const.Level.INFO and log.type == const.Log.INFO):
            print(log, file=self.stream, flush=True)

    def close(self):
        if self.out != 'stdout':
            self.stream.close()


class Logger(AsyncAgent):
    def __init__(self, tag, standalone=True):
        super(Logger, self).__init__()

        self.standalone = standalone
        base_dir = Path(os.getcwd()) / 'logs'
        tag += '-' + get_name_hash(3)

        self.sinks = [
            Sink(const.Level.ALL),
            # Sink(const.Level.INFO, base_dir / f'{tag}.info'),
            Sink(const.Level.CRITICAL, base_dir / f'{tag}.err'),
            Sink(const.Level.ALL, base_dir / f'{tag}.detail')
        ]

        if standalone:
            self.queue = queue.Queue()
            self.run_coroutine_threadsafe('', self.push_log)
            self.thread = self.run_in_fork()
        else:
            self.queue = asyncio.Queue()
            self.run_coroutine('', self.push_log)

    def close(self):
        self.log_info('----- End of Log -----')
        self.queue.put_nowait(Log(None, const.Log.CLOSE, ''))
        self.thread.join()
        for sink in self.sinks:
            sink.close()

    def log_info(self, msg):
        self._log(const.Log.INFO, msg)

    def log_warning(self, msg):
        self._log(const.Log.WARNING, msg)

    def log_error(self, msg):
        self._log(const.Log.ERROR, msg)

    def _log(self, level, msg):
        try:
            self.queue.put_nowait(Log(Timestamp.now(), level, msg))
        except Exception:
            print('Log queue full')

    async def push_log(self):
        if self.standalone:
            log = self.queue.get()
        else:
            log = await self.queue.get()

        if log.type != const.Log.CLOSE:
            for sink in self.sinks:
                sink.dump(log)
            return True

        self.loop.stop()
        return False
