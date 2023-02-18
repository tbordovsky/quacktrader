from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from finta import TA
import yfinance


class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        self.sma1 = self.I(TA.SMA, self.data.df, self.n1)
        self.sma2 = self.I(TA.SMA, self.data.df, self.n2)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()


goog = yfinance.Ticker('goog')
ohlc = goog.history(interval='1d', start='2004-08-19', end='2013-03-01')
bt = Backtest(ohlc, SmaCross,
              cash=10000, commission=.002,
              exclusive_orders=True)

output = bt.run()
print(output)
bt.plot()