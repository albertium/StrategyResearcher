
# from strategyrunner.data import DataManager, HistoricalDataHandler
# from strategyrunner.strategy import MomentumStrategy, BuyAndHold
# from strategyrunner.execution import SimulatedExecutionHandler
# from strategyrunner import Trader, Portfolio
# import time

# # bt = Trader(MomentumStrategy, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
# bt = Trader(BuyAndHold, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
# # bt.set_tickers(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV"])
# bt.set_tickers(['VFINX'])
# bt.set_dates("1988-08-01", "2012-12-31")
# bt.set_capital(10000)
# start = time.clock()
# print("total: ", time.clock() - start, "s\n")


# with DataManager("data/test.db") as dm:
#     # data = dm.get_data(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV", "IGSB"], "2016-01-01", "2017-02-28")
#     data = dm.get_data(["AAPL"], "1988-08-01", "2018-10-01")
#
# print(data.head())

from strategyrunner import Trader
from strategyrunner.strategy import MomentumStrategy
from strategyrunner.const import Broker


trader = Trader(MomentumStrategy)
trader.set_capital(10000)
trader.set_broker(Broker.SIMULATED)
trader.set_tickers(['AAPL', 'GOOG', 'FB', 'AMZN', 'TSLA', 'GS', 'JPM'])
trader.set_time('2015-01-01', '2018-11-01')
trader.trade()


