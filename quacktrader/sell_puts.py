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
    return ['$SPX.X', '$NDX.X', '$RUT.X', '$DJX.X', '$OEX.X']


try:
    tda_client = auth.client_from_token_file(TDA_TOKEN_PATH, TDA_API_KEY)
except FileNotFoundError:
    # go through the oauth2 workflow manually, but with a little help
    tda_client = auth.client_from_manual_flow(TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH)

symbols: List[str] = select_symbols()
from_date = datetime.date.today() + datetime.timedelta(days=21)
to_date = from_date + datetime.timedelta(days=42)
put_options = []

for symbol in symbols:
    response = tda_client.get_option_chain(
        symbol=symbol,
        contract_type=Client.Options.ContractType.PUT,
        strategy=Client.Options.Strategy.SINGLE,
        strike_range=Client.Options.StrikeRange.STRIKES_BELOW_MARKET,
        from_date=from_date,
        to_date=to_date)
    assert response.status_code == httpx.codes.OK, response.raise_for_status()
    # print(json.dumps(response.json(), indent=4))

    option_chain = response.json()
    put_expdate_map = option_chain['putExpDateMap']
    strikes_per_expiry_date = put_expdate_map.values()
    puts_per_strike = map(lambda x: x.values(), strikes_per_expiry_date)
    put_options = itertools.chain(put_options, *puts_per_strike)
    # print(list(put_options)[0]) # in the case of Strategy.SINGLE each contract only contains one option leg, but make sure to account for multiple 

    accounts_response = tda_client.get_accounts()
    assert accounts_response.status_code == 200, accounts_response.raise_for_status()
    # print(json.dumps(response.json(), indent=4))

accounts = accounts_response.json()
buying_power = 1000000  # accounts[0]['securitiesAccount']['currentBalances']['buying_power'] * .12 # this is an arbitrarily small portion of our capital

puts = filter(lambda put: put[0]['strikePrice'] * 100 <= buying_power, put_options)
puts = filter(lambda put: put[0]['totalVolume'] > 0, puts)
puts = filter(lambda put: not put[0]['inTheMoney'], puts)
puts = filter(lambda put: put[0]['delta'] > -.175, puts)
# print(list(puts))

# and the best one is!...
puts = sorted(puts, key = lambda put: (put[0]['mark'] / put[0]['strikePrice']) / put[0]['daysToExpiration'], reverse=True)
the_one_put = puts[0][0]
print(the_one_put)
contract_type = the_one_put['putCall']
option_symbol = the_one_put['symbol']
theoretical_premium: float = the_one_put['mark'] * 100 
profit = theoretical_premium # - cost_to_open ## this ideally will account for the cost of the trade which will be higher for more complex positions
stake: float = the_one_put['strikePrice'] * 100
alpha: float = 0 # because I didn't do the hard part yet lol
delta: float = the_one_put['delta']
expected_value = profit * (1 + delta)
days_to_expiration = the_one_put['daysToExpiration']
return_on_risk = (expected_value / stake) * 100
annualized_return = return_on_risk * (365 / days_to_expiration)

print(f"Sell {contract_type} on {option_symbol} to collect a ${theoretical_premium} premium for a stake of ${stake}.")
print(f"Given a delta of {delta}, an alpha of {alpha}, and a profit of ${profit}, the expected value of this position is {expected_value}")
print(f"This represents a hypothetical gain of {return_on_risk:.2f}% over {days_to_expiration} days, or an annualized return of {annualized_return:.2f}%.")

