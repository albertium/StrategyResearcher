
from strategytester.data import DataManager, HistoricalDataHandler
from strategytester.strategy import MomentumStrategy, BuyAndHold
from strategytester.execution import SimulatedExecutionHandler
from strategytester import BackTest, Portfolio

# # bt = BackTest(MomentumStrategy, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
# bt = BackTest(BuyAndHold, Portfolio, HistoricalDataHandler, SimulatedExecutionHandler)
# # bt.set_tickers(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV"])
# bt.set_tickers(['VFINX', 'VFISX'])
# bt.set_dates("1988-08-01", "2012-12-31")
# bt.set_capital(10000)
# bt.run()



with DataManager("data/test.db") as dm:
    # data = dm.get_data(["CWI", "HYG", "IAU", "ITB", "SMH", "TLT", "VGK", "VOO", "XBI", "XLI", "XLV", "IGSB"], "2016-01-01", "2017-02-28")
    data = dm.get_data(["VFISX"], "1988-08-01", "2012-12-31")

print(data.head())

