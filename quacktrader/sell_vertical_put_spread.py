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
from_date = datetime.date.today() + datetime.timedelta(days=30)
to_date = from_date + datetime.timedelta(days=60)
option_strategies = []

for symbol in symbols:
    response = tda_client.get_option_chain(
        symbol=symbol,
        contract_type=Client.Options.ContractType.PUT,
        strategy=Client.Options.Strategy.VERTICAL,
        strike_range=Client.Options.StrikeRange.OUT_OF_THE_MONEY,
        from_date=from_date,
        to_date=to_date)
    assert response.status_code == 200, response.raise_for_status()
    # print(json.dumps(response.json(), indent=4))

    strategy_chain = response.json()
    if (strategy_chain['status'] == 'FAILED'):
        raise Exception("The API request failed.")

    for expiry_date in strategy_chain['monthlyStrategyList']:
        for option_strategy in expiry_date['optionStrategyList']:
            # propagate some of the parent data to the children for convenience
            option_strategy['symbol'] = strategy_chain['symbol']
            option_strategy['daysToExpiration'] = expiry_date['daysToExp']
            option_strategies.append(option_strategy)



accounts_response = tda_client.get_accounts()
assert accounts_response.status_code == 200, accounts_response.raise_for_status()
# print(json.dumps(response.json(), indent=4))

accounts = accounts_response.json()
buying_power = accounts[0]['securitiesAccount']['currentBalances']['buyingPower'] * .12 # this is an arbitrarily small portion of our capital
# buying_power = 1000000

# pare down the list so we don't have to make so many additional api calls
option_strategies = filter(lambda strategy: (strategy['primaryLeg']['strikePrice'] - strategy['secondaryLeg']['strikePrice']) * 100 <= buying_power, option_strategies)
option_strategies = filter(lambda strategy: strategy['primaryLeg']['totalVolume'] and strategy['secondaryLeg']['totalVolume'] > 0, option_strategies)
option_strategies = filter(lambda strategy: strategy['primaryLeg']['range'] == 'OTM', option_strategies)
viable_option_strategies = []

for option_strategy in option_strategies:
    # find stats for the primary leg
    option_chain_response = tda_client.get_option_chain(
        symbol=option_strategy['symbol'],
        contract_type=Client.Options.ContractType.PUT,
        strategy=Client.Options.Strategy.SINGLE,
        strike_range=Client.Options.StrikeRange.OUT_OF_THE_MONEY,
        from_date=from_date,
        to_date=to_date)
    assert option_chain_response.status_code == 200, option_chain_response.raise_for_status()
    # print(json.dumps(option_chain_response.json(), indent=4))

    option_chain = option_chain_response.json()
    put_expdate_map = option_chain['putExpDateMap']
    strikes_per_expiry_date = put_expdate_map.values()
    puts_per_strike = map(lambda x: x.values(), strikes_per_expiry_date)
    put_options = itertools.chain(*puts_per_strike)
    primary_leg_option_chain = next((put_option for put_option in put_options if put_option[0]['symbol'] == option_strategy['primaryLeg']['symbol']), None)
    if primary_leg_option_chain is None:
        # i don't understand why this would happen but it does, maybe debug it later
        continue

    for key in ['delta', 'gamma', 'theta', 'vega', 'rho', 'volatility', 'theoreticalVolatility']:
        option_strategy[key] = primary_leg_option_chain[0][key]

    viable_option_strategies.append(option_strategy)



# narrow it down
viable_option_strategies = filter(lambda strategy: strategy['delta'] > -0.175, viable_option_strategies)
# iv > hv ## is that actually what theoreticalVolatility and volatility are?
viable_option_strategies = filter(lambda strategy: strategy['theoreticalVolatility'] > strategy['volatility'], viable_option_strategies)

# look at the top five
viable_option_strategies = sorted(viable_option_strategies, key = lambda strategy: (((strategy['strategyAsk'] - strategy['strategyBid']) / 2) / strategy['daysToExpiration']), reverse=True)
for the_one_strategy in viable_option_strategies[:5]:
    underlying_symbol = the_one_strategy['symbol']
    print(f"The best strategy is: \n {the_one_strategy}")

    theoretical_premium: float = (the_one_strategy['strategyAsk'] - the_one_strategy['strategyBid']) / 2 * 100 
    profit = theoretical_premium # - cost_to_open ## this ideally will account for the cost of the trade which will be higher for more complex positions
    stake: float = (the_one_strategy['primaryLeg']['strikePrice'] - the_one_strategy['secondaryLeg']['strikePrice']) * 100
    alpha: float = 0 # because I didn't do the hard part yet lol
    delta: float = the_one_strategy['delta']
    expected_value = profit * (1 + delta)
    days_to_expiration = the_one_strategy['daysToExpiration']
    return_on_risk = (expected_value / stake) * 100
    annualized_return = return_on_risk * (365 / days_to_expiration)

    print(f"Sell vertical put spread on {underlying_symbol} to collect a ${theoretical_premium} premium for a stake of ${stake} per contract.")
    print(f"Given a delta of {delta}, an alpha of {alpha}, and a profit of ${profit}, the expected value of this position is ${expected_value} per contract.")
    print(f"This represents a hypothetical gain of {return_on_risk:.2f}% over {days_to_expiration} days, or an annualized return of {annualized_return:.2f}%.")

