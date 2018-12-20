
import pandas as pd
from scipy.stats import norm
from matplotlib import pyplot as plt

from strategyrunner.data import DataManager


def get_inverse_vol_weights(prices: pd.DataFrame, lookback=90):
    sigmas = prices.pct_change().rolling(lookback).std().dropna()
    sigmas.VTI.plot()
    weights = 1 / sigmas
    return weights.div(weights.sum(axis=1), axis=0)


def get_correlation_adjustement(prices: pd.DataFrame, lookback=90):
    cors = prices.pct_change().rolling(lookback).corr().dropna().groupby(by='date').mean()
    scores = 1 - cors.sub(cors.mean(axis=1), axis=0).div(cors.std(axis=1), axis=0).apply(norm.cdf)
    return scores.div(scores.sum(axis=1), axis=0)


def combine_weights(w1, w2, alpha=1):
    new_w = w1 * (1 + alpha * (w2 - 1 / w2.shape[1]))
    return new_w.div(new_w.sum(axis=1), axis=0)


tickers = ['VTI', 'EFA', 'IEF', 'TLT']
with DataManager('./data/test.db') as db:
    data = db.get_data(tickers, '2017-01-01')

w1 = get_inverse_vol_weights(data.close)
w2 = get_correlation_adjustement(data.close, 14)
final_w = combine_weights(w1, w2)
print(w1.tail(3))
print(w2.tail(3))
print(final_w.tail(3))