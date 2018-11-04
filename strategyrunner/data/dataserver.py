
import zmq
import os
from enum import Enum
from strategyrunner.service import Service, ServiceType
from strategyrunner.data import DataManager, HistoricalDataObject, RealTimeDataObject


class RequestType(Enum):
    HISTORICAL = 'H'
    REAL = 'L'


class DataServer(Service):
    def __init__(self):
        self.base_dir = f'{os.getcwd()}/data/test.db'

    @Service.service(ServiceType.Server, zmq.REP, [5555, 5556, 5557])
    async def answer_data_request(self, socket: zmq.Socket):
        request = await socket.recv_string()
        if request == RequestType.HISTORICAL:
            data_obj = HistoricalDataObject(await self.retrieve_data_from_db())
        elif request == RequestType.REAL:
            data_obj = RealTimeDataObject(5558)
        else:
            print(f'unrecognized request {request}')
            return

        socket.send_pyobj(data_obj)

    @Service.service(ServiceType.Server, zmq.PUB, 5558)
    async def broadcast_data(self):
        pass

    @Service.job
    def retrieve_data_from_db(self, tickers):
        with DataManager("data/test.db") as dm:
            self.__data = dm.get_data(tickers, start_date, end_date)