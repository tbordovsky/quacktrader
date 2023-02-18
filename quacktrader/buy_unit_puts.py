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


def select_symbols() -> List[str]:
    return ['$SPX.X', '$NDX.X', '$RUT.X', '$DJX.X', '$OEX.X']


try:
    tda_client = auth.client_from_token_file(TDA_TOKEN_PATH, TDA_API_KEY)
except FileNotFoundError:
    # go through the oauth2 workflow manually, but with a little help
    tda_client = auth.client_from_manual_flow(TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH)

symbols: List[str] = select_symbols()
# only look for "front-month options"
from_date = datetime.date.today() + datetime.timedelta(days=14)
to_date = from_date + datetime.timedelta(days=60)
put_options = []

for symbol in symbols:
    response = tda_client.get_option_chain(
        symbol=symbol,
        contract_type=Client.Options.ContractType.PUT,
        strategy=Client.Options.Strategy.SINGLE,
        strike_range=Client.Options.StrikeRange.OUT_OF_THE_MONEY,
        from_date=from_date,
        to_date=to_date)
    assert response.status_code == 200, response.raise_for_status()
    # print(json.dumps(response.json(), indent=4))

    option_chain = response.json()
    put_expdate_map = option_chain['putExpDateMap']
    strikes_per_expiry_date = put_expdate_map.values()
    puts_per_strike = map(lambda x: x.values(), strikes_per_expiry_date)
    put_options = itertools.chain(put_options, *puts_per_strike)
    # print(next(put_options)) # in the case of Strategy.SINGLE each contract only contains one option leg, but make sure to account for multiple 

accounts_response = tda_client.get_accounts()
assert accounts_response.status_code == 200, accounts_response.raise_for_status()
# print(json.dumps(accounts_response.json(), indent=4))

accounts_data = accounts_response.json()
buying_power = accounts_data[0]['securitiesAccount']['currentBalances']['buyingPower'] # this is an arbitrarily small portion of our capital

# we have to be able to afford it
puts = filter(lambda put: put[0]['mark'] * 100 <= buying_power, put_options)
# puts = filter(lambda put: put[0]['totalVolume'] > 0, puts) # we might be the first one to write this contract
# puts = filter(lambda put: not put[0]['inTheMoney'], puts)

# unit puts will have a delta of less than 5 and little to no gamma or vega
puts = filter(lambda put: put[0]['delta'] > -.05, puts)
puts = filter(lambda put: put[0]['gamma'] < .02, puts)
puts = filter(lambda put: put[0]['vega'] < .02, puts)
# print(list(puts))

# and the best one is!...
the_one_put = max(puts, key = lambda put: put[0]['strikePrice'])[0]
print(the_one_put)
contract_type = the_one_put['putCall']
option_symbol = the_one_put['symbol']
theoretical_premium = the_one_put['mark'] * 100

# how many contracts should we buy?
# 5 to 10% of allocated trading money (not the total account value)
# is longMarketValue the same as allocated trading money??
long_margin_value = accounts_data[0]['securitiesAccount']['currentBalances']['longMarketValue']
total_capital = accounts_data[0]['securitiesAccount']['currentBalances']['liquidationValue']
stake = min(long_margin_value * .05, total_capital * .02)
number_contracts = int(stake / theoretical_premium)

print(f"Buy {number_contracts}x{contract_type} on {option_symbol} for a ${theoretical_premium} premium to insure against black swan events.")

