import numpy as np
import pandas as pd
from pandas_datareader import data as wb
import matplotlib.pyplot as plt

assets = ['MSFT','UNH']

pf_data = pd.DataFrame()
for t in assets:
    pf_data[t] = wb.DataReader(t, data_source='yahoo', start='2015-1-1')['Adj Close']
    
(pf_data / pf_data.iloc[0]*100).plot(figsize=(15,6))

log_returns = np.log(pf_data / pf_data.shift(1))
log_returns.mean()*250

num_assets = len(assets)

weights = np.random.random(num_assets)
weights /= np.sum(weights)

pfolio_returns = []
pfolio_volatilities = []

for x in range(1000):
    weights = np.random.random(num_assets)
    weights /= np.sum(weights)
    
    pfolio_returns.append(np.sum(weights*log_returns.mean())*252)
    pfolio_volatilities.append(np.sqrt(np.dot(weights.T, np.dot(log_returns.cov()*250, weights))))
    
pfolio_returns = np.array(pfolio_returns)
pfolio_volatilities = np.array(pfolio_volatilities)

portfolios = pd.DataFrame({'Return': pfolio_returns,'Volatility': pfolio_volatilities})

portfolios.plot(x='Volatility',y='Return', kind='scatter', figsize=(10,6))
#plt.axis([0,])
plt.xlabel('Expected Volatility')
plt.ylabel('Expected Return')

print(f"Expected Portfolio Return: {round(np.sum(weights * log_returns.mean())*252*100,2)}%")
print(f"Expected Portfolio Variance: {round(100*np.dot(weights.T, np.dot(log_returns.cov() *252, weights)),2)}%")
print(f"Expected Portfolio Volatility: {round(100*np.sqrt(np.dot(weights.T, np.dot(log_returns.cov()*252, weights))),2)}%")

plt.show()