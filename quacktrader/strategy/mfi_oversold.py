from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from finta import TA
import yfinance


class MFIOversold(Strategy):
    def init(self):
        self.mfi = self.I(TA.MFI, self.data.df)

    def next(self):
        if (self.mfi < 20):
            # oversold
            self.buy()
        elif (self.mfi > 80):
            # overbought
            self.sell()


goog = yfinance.Ticker('goog')
ohlc = goog.history(interval='1d', start='2004-08-19', end='2013-03-01')
bt = Backtest(ohlc, MFIOversold,
              cash=10000, commission=.002,
              exclusive_orders=True)

output = bt.run()
print(output)
bt.plot()