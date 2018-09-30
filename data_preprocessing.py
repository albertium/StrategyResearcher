
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def append_returns(df, days):
    if days == 0:
        raise ValueError("days should be non-zero")

    dates = df.index.tolist()
    shifted = [y for y in [x - timedelta(days=days) for x in dates] if dates[0] <= y <= dates[-1]]
    # if days > 0:
    #     matched = [next(date for date, date_next in zip(dates[:-1], dates[1:]) if date_next > x) for x in shifted]
    # else:
    #     matched = [next(date for date, date_next in zip(dates[:-1], dates[1:]) if date_next > x) for x in shifted]
    # ret = data[-len(matched):]["Close"].values / data.loc[matched]["Close"].values - 1
    # columns = pd.MultiIndex.from_tuples([("Return", x) for x in data.columns.levels[1].tolist()])
    # to_append = pd.DataFrame(ret, index=data[-len(matched):].index, columns=columns)
    # a = pd.concat([data, to_append], axis=1)
    # a.head(30)


def plot_push_reaction(df, push_days, react_days, col="Close"):
    rets = pd.concat([df[col].pct_change(periods=push_days), df[col].pct_change(periods=-react_days)], axis=1).dropna()
    rets = rets.reorder_levels([1, 0], axis=1).sort_index(axis=1)

    tickers = rets.columns.levels[0].tolist()
    for ticker in tickers:
        rets[ticker].plot.scatter(x='x', y='y')

