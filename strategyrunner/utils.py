
from pandas.tseries.offsets import DateOffset, BDay
import dateutil.parser as du
import json
import os
import pathlib
import numpy as np
import string


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


def load_config(file=None):
    if file is None or not pathlib.Path(file).is_file():
        file = f'{os.getcwd()}/strategyrunner/config/default.config'
    with open(file, 'r') as f:
        config = json.load(f)
    return config


alphabets = list(string.digits + string.ascii_uppercase)


def get_name_hash():
    return ''.join(np.random.choice(alphabets, 5))

