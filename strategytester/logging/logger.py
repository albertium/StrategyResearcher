
import queue
from threading import Lock
import os
from pathlib import Path
from .log import Log, Level
from .sink import Sink, SinkLevel


class Logger:
    def __init__(self):
        self.cache = queue.Queue()
        self.lock = Lock()
        self.timer = None
        base_dir = Path(os.getcwd()) / 'logs'
        self.sinks = [
            Sink(SinkLevel.CRITICAL),
            Sink(SinkLevel.INFO, base_dir / 'strategy1.info'),
            Sink(SinkLevel.CRITICAL, base_dir / 'strategy1.err'),
            Sink(SinkLevel.ALL, base_dir / 'strategy1.detail')
        ]

    def set_timer(self, timer):
        self.timer = timer

    def close(self):
        for sink in self.sinks:
            sink.close()

    def log_info(self, msg):
        self._log(Level.INFO, msg)

    def log_warning(self, msg):
        self._log(Level.WARNING, msg)

    def log_error(self, msg):
        self._log(Level.ERROR, msg)

    def _log(self, level, msg):
        self.cache.put(Log(self.timer.now(), level, msg))
        self._flush()

    def _flush(self):
        if self.lock.acquire(blocking=False):
            while True:
                try:
                    log = self.cache.get_nowait()
                    for sink in self.sinks:
                        sink.dump(log)
                except queue.Empty:
                    break
            self.lock.release()
