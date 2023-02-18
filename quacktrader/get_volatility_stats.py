import datetime
from functools import reduce
import itertools
from operator import getitem
import operator
from typing import List
from constants import TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH
from tda import auth
from tda.client import Client
import json
import httpx


def select_symbols() -> List[str]:
    # return ['$SPX.X', '$NDX.X', '$RUT.X', '$DJX.X', '$OEX.X']
    return ['SPY']


try:
    tda_client = auth.client_from_token_file(TDA_TOKEN_PATH, TDA_API_KEY)
except FileNotFoundError:
    # go through the oauth2 workflow manually, but with a little help
    tda_client = auth.client_from_manual_flow(TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH)

symbols: List[str] = select_symbols()
from_date = datetime.date.today() + datetime.timedelta(days=21)
to_date = from_date + datetime.timedelta(days=42)
put_options = []


response = tda_client.search_instruments(symbols=symbols, projection=Client.Instrument.Projection.FUNDAMENTAL)
assert response.status_code == httpx.codes.OK, response.raise_for_status()
print(json.dumps(response.json(), indent=4))
