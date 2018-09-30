
from pandas.tseries.offsets import DateOffset, BDay
import dateutil.parser as du
from datetime import datetime


def rdate(period):
    ind = period[-1]
    if period[-1] == 'd':
        return DateOffset(days=int(period[:-1]))
    elif period[-1] == 'b':
        return BDay(int(period[:-1]))
    elif period[-1] == 'm':
        return DateOffset(months=int(period[:-1]))
    elif period[-1] == 'y':
        return DateOffset(years=int(period[:-1]))

    raise ValueError("Unrecognized delta type")


def parse_time(time):
    if isinstance(time, str):
        return du.parse(time)
    return time
