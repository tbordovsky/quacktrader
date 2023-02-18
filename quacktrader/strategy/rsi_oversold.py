from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from finta import TA
import yfinance


class RSIOversold(Strategy):
    def init(self):
        self.rsi = self.I(TA.RSI, self.data.df)

    def next(self):
        if (self.rsi < 30):
            # oversold
            self.buy()
        elif (self.rsi > 70):
            # overbought
            self.sell()


goog = yfinance.Ticker('goog')
ohlc = goog.history(interval='1d', start='2004-08-19', end='2013-03-01')
bt = Backtest(ohlc, RSIOversold,
              cash=10000, commission=.002,
              exclusive_orders=True)

output = bt.run()
print(output)
bt.plot()