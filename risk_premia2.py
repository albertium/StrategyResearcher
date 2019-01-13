
import pandas as pd
import numpy as np
from scipy.stats import norm
import plotly.offline as py
import plotly.graph_objs as go

from strategyrunner.data import DataManager


path = 'C:/Users/Albert/RProjects/risk-premia-algo-boot-camp/'

rets = pd.read_csv(path + 'ret.csv', index_col=0, parse_dates=True)
wgts = pd.read_csv(path + 'wgt.csv', index_col=0, parse_dates=True)


def calculate_performance(rets: pd.DataFrame, weights: pd.DataFrame):
    if set(rets.columns) != set(weights.columns):
        print(f'indices do not match:\n rets: {rets.columns}\n  weights: {weights.columns}')
        raise ValueError('indices do not match')

    # performance metrics
    weights = weights.reindex(rets.index, method='ffill').shift(1).dropna()
    portfolio_rets = (rets * weights).dropna().sum(axis=1)
    cagr = (portfolio_rets + 1).prod() ** (252 / portfolio_rets.shape[0]) - 1
    vol = portfolio_rets.std() * np.sqrt(252)
    sharpe = cagr / vol

    # cost metrics
    trade_size = (weights - weights.shift(1)).dropna().abs().sum(axis=1)
    trade_size = trade_size[trade_size != 0].mean()  # todo: test the extreme, say flip the whole thing everyday, everything week

    # plot
    plot_data = (1 + portfolio_rets).cumprod()
    trace = go.Scatter(x=plot_data.index, y=plot_data)
    py.plot([trace])

    return {'cagr': cagr, 'vol': vol, 'sharpe': sharpe, 'trade_size': trade_size}


class AlphaCalculator:
    def __init__(self, prices: pd.DataFrame):
        self.prices = prices
        self.normalized_prices = prices.div(prices.iloc[0], axis=0)
        self.rets = prices.pct_change()

    # --- utils ---
    @staticmethod
    def convert_zscore(self, alpha: pd.DataFrame, gaussian=False):
        tmp = alpha.sub(alpha.mean(axis=1), axis=0).div(alpha.std(axis=1), axis=0)
        if gaussian:
            return tmp.apply(norm.cdf)
        return tmp

    @staticmethod
    def combine_weights(wgt1: pd.DataFrame, wgt2: pd.DataFrame, shrinkage=1):
        common_index = wgt1.index.intersection(wgt2.index)
        wgt = wgt1.loc[common_index] * (1 + shrinkage * wgt2.loc[common_index])
        return wgt.div(wgt.sum(axis=1), axis=0)

    # --- base inverse volatility ---
    def get_inverse_vol_weights(self, lookback=90):
        sigmas = self.rets.rolling(lookback).std().dropna()
        weights = 1 / sigmas
        return weights.div(weights.sum(axis=1), axis=0)

    def get_correlation_adjustment(self, lookback=90):
        cors = self.rets.rolling(lookback).corr().dropna().groupby(level=0).mean()
        scores = 1 - cors.sub(cors.mean(axis=1), axis=0).div(cors.std(axis=1), axis=0).apply(norm.cdf)
        return scores.div(scores.sum(axis=1), axis=0) - 1 / scores.shape[1]

    # --- momentum ---
    def get_momentum_weight(self, lookback=66):
        pass




tickers = ['VTI', 'EFA', 'IEF', 'TLT']
with DataManager('./data/test.db') as db:
    data = db.get_data(tickers, '2010-01-01')  # type: pd.DataFrame

alphas = AlphaCalculator(data.close)
wgt1 = alphas.get_inverse_vol_weights()
wgt2 = alphas.get_correlation_adjustment(lookback=90)
final_weight = alphas.combine_weights(wgt1, wgt2, shrinkage=1)
down_sampled = final_weight.iloc[5::22]

res = calculate_performance(data.close.pct_change(), down_sampled)
print(res)
