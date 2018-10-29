
import zmq


class DataServer:
    def __init__(self):
        self.context = zmq.Context()

    def run(self):
        self.socket = self.context.socket(zmq)