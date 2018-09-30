
from strategytester.data_manager import DataManager

with DataManager("data/test.db") as dm:
    data = dm.get_data(["AAPL"], "2016-01-01", "2017-02-28")

print(data.head())