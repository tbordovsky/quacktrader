from dataclasses import dataclass
from datetime import timedelta, datetime

@dataclass
class Forecast:
    timestamp: datetime
    direction: int
    timeframe: timedelta