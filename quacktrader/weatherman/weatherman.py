import datetime
from numbers import Number
from typing import Sequence
from quacktrader.weatherman.forecast import Forecast
from finta import TA
import pandas as pd

def crossover(series1: Sequence, series2: Sequence) -> bool:
    """
    Return `True` if `series1` just crossed over (above)
    `series2`.

        >>> crossover(self.data.Close, self.sma)
        True
    """
    series1 = (
        series1.values if isinstance(series1, pd.Series) else
        (series1, series1) if isinstance(series1, Number) else
        series1)
    series2 = (
        series2.values if isinstance(series2, pd.Series) else
        (series2, series2) if isinstance(series2, Number) else
        series2)
    try:
        return series1[-2] < series2[-2] and series1[-1] > series2[-1]
    except IndexError:
        return False

class Weatherman:
    def make_forecast(self, ohlc: pd.DataFrame) -> Forecast:
        sma_50 = TA.SMA(ohlc, period=50, column='close')
        sma_100 = TA.SMA(ohlc, period=100, column='close')
        sma_200 = TA.SMA(ohlc, period=200, column='close')
        timestamp = ohlc.index[-1]

        direction = 0
        if crossover(sma_50, sma_100):
            direction = 1
        elif crossover(sma_100, sma_50):
            direction = -1
        forecast_30d = Forecast(timestamp, direction, datetime.timedelta(days=30))

        direction = 0
        if crossover(sma_50, sma_200):
            direction = 1
        elif crossover(sma_200, sma_50):
            direction = -1
        forecast_60d = Forecast(timestamp, direction, datetime.timedelta(days=60))

        if forecast_30d.direction == forecast_60d.direction:
            return forecast_60d
        elif forecast_30d == 0:
            return forecast_60d
        else:
            return forecast_30d