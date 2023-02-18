import datetime
from typing import List
import yfinance

from quacktrader.weatherman.weatherman import Weatherman


def _select_symbols() -> List[str]:
    return ['goog']
    # return ['$SPX.X', '$NDX.X', '$RUT.X', '$DJX.X', '$OEX.X']

# get data for these symbols
symbols: List[str] = _select_symbols()
from_date = datetime.date.today() - datetime.timedelta(days=400)

weatherman = Weatherman()

for symbol in symbols:
    ticker = yfinance.Ticker(symbol)
    ohlc = ticker.history(period='1d', interval='1d', start=str(from_date))
    forecast = weatherman.make_forecast(ohlc)
    print(forecast)

# ohlc.tail()

# apply finta indicators to derive Direction (opinion), Time Frame (of the opinion)

# get option chain for symbols

# query for (or derive) the Implied Volatility, Historical Volatility, and Volatility Skew

# use these five factors to determine strategy options for all symbols (there may be no strategy as well)

# it may be possible to backtest this class with optopsy, which canvases for the best trades in an option chain