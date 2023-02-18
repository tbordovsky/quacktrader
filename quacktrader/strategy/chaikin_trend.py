from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from finta import TA
import yfinance


class ChaikinTrend(Strategy):
    def init(self):
        self.chaikin_oscillator = self.I(TA.CHAIKIN, self.data.df)

    def next(self):
        if (self.chaikin_oscillator > 0):
            self.buy()
        else:
            self.sell()

goog = yfinance.Ticker('goog')
ohlc = goog.history(interval='1d', start='2004-08-19', end='2013-03-01')
bt = Backtest(ohlc, ChaikinTrend,
              cash=10000, commission=.002,
              exclusive_orders=True)

output = bt.run()
print(output)
bt.plot()