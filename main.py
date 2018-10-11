
from strategytester.data import DataManager, HistoricalDataHandler
from strategytester.strategy import MomentumStrategy
from strategytester.execution import SimulatedExecutionHandler
from strategytester import BackTest, Portfolio

bt = BackTest(MomentumStrategy, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
bt.set_tickers(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV"])
bt.set_dates("2016-01-01", "2017-02-01")
bt.set_capital(10000)
bt.run()



# with DataManager("data/test.db") as dm:
#     data = dm.get_data(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV", "IGSB"], "2016-01-01", "2017-02-28")
#
# print(data.head())

