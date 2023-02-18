from math import isnan
import pprint
import yfinance
import montecarlo
import pandas
import matplotlib.pyplot as plotter

# from pandas_datareader import data
# df = data.get_data_yahoo("SPY")

goog = yfinance.Ticker('spy')
ohlc = goog.history(interval='1d', start='2004-08-19', end='2013-03-01')
leverage = 1
ohlc['return'] = leverage * ohlc['Close'].pct_change().fillna(0)

def income(i: pandas.Timestamp):
    """$1000/mo"""
    if i.is_month_start:
        return 10000
    else:
        return 0

ohlc['contributions'] = ohlc.index.map(income)

def cumulative_balance(df):
    results = []
    total = 300000
    for group in df.groupby('Date').groups.values():
        result = []
        for percent_return, contributions in df.loc[group, ['return', 'contributions']].values:
            if isnan(percent_return):
                total += contributions
            else:
                total = (total * (1 + percent_return)) + contributions
            result.append(total)
        results.append(pandas.Series(result, index=group))
    return pandas.concat(results).reindex(df.index)

ohlc['balance'] = cumulative_balance(ohlc)
# print(ohlc.head)

mc = ohlc['balance'].montecarlo(sims=2, bust=-0.1, goal=100)
pprint.pprint(mc.stats)
pprint.pprint(mc.maxdd)
mc.plot(title="SPY Returns Monte Carlo Simulations")  # optional: , figsize=(x, y)

# plotter.plot(ohlc['balance'])
# plotter.show()