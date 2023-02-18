from datetime import datetime
import numpy as np
import pandas as pd
from pandas_datareader import data as wb


# https://github.com/eliasmelul/finance_portfolio

#Import the data of any stock of set of stocks
def import_stock_data(tickers, start = '2010-1-1', end = datetime.today().strftime('%Y-%m-%d')):
    data = pd.DataFrame()
    if len([tickers]) ==1:
        data[tickers] = wb.DataReader(tickers, data_source='yahoo', start = start)['Adj Close']
        data = pd.DataFrame(data)
    else:
        for t in tickers:
            data[t] = wb.DataReader(t, data_source='yahoo', start = start)['Adj Close']
    return(data)

# Compute beta function   
def compute_beta(data, stock, market):
    log_returns = np.log(data / data.shift(1))
    cov = log_returns.cov()*250
    cov_w_market = cov.loc[stock,market]
    market_var = log_returns[market].var()*250
    return cov_w_market/market_var

#Compute risk adjusted return function
def compute_capm(data, stock, market, riskfree = 0.025, riskpremium = 'market'):
    log_returns = np.log(data / data.shift(1))
    if riskpremium == 'market':
        riskpremium = (log_returns[market].mean()*252) - riskfree
    beta = compute_beta(data, stock, market)
    return (riskfree + (beta*riskpremium))
   
#Compute Sharpe Ratio
def compute_sharpe(data, stock, market, riskfree = 0.025, riskpremium='market'):
    log_returns = np.log(data / data.shift(1))
    ret = compute_capm(data, stock, market, riskfree, riskpremium)
    return ((ret-riskfree)/(log_returns[stock].std()*250**0.5))
    
# All in one function
def stock_CAPM(stock_ticker, market_ticker, start_date = '2010-1-1', riskfree = 0.025, riskpremium = 'set'):
    data = import_stock_data([stock_ticker,market_ticker], start = start_date)
    beta = compute_beta(data, stock_ticker, market_ticker)
    capm = compute_capm(data, stock_ticker, market_ticker)
    sharpe = compute_sharpe(data, stock_ticker, market_ticker)
    #listcapm = [beta,capm,sharpe]
    capmdata = pd.DataFrame([beta,capm,sharpe], columns=[stock_ticker], index=['Beta','Return','Sharpe'])
    return capmdata.T
    
# stock_CAPM("AAPL","^GSPC")