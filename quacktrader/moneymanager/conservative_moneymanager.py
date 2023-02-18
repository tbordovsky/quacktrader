from quacktrader.constants import TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH
from tda import auth, client
import json
from tda.client import Client

from quacktrader.moneymanager.moneymanager import MoneyManager

try:
    tda_client = auth.client_from_token_file(TDA_TOKEN_PATH, TDA_API_KEY)
except FileNotFoundError:
    # go through the oauth2 workflow manually, but with a little help
    tda_client = auth.client_from_manual_flow(TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH)

class ConservativeMoneyManger(MoneyManager):
    """
    Manage investment capital based on two simple rules:
    1. Never risk more than 2% of capital on any single trade.
    2. If in any single month the account loses more than 6%, stop trading for the rest of the month.
    """

    def get_risk_capital(self) -> int:
        """Only allow cash-secured positions for now"""
        accounts_response = tda_client.get_accounts(fields=Client.Account.Fields.POSITIONS)
        assert accounts_response.status_code == 200, accounts_response.raise_for_status()
        # print(json.dumps(accounts_response.json(), indent=4))

        accounts_data = accounts_response.json()
        positions = accounts_data[0]['securitiesAccount']['positions']
        current_day_profit_loss_percentage = sum(position['currentDayProfitLossPercentage'] for position in positions)
        if (current_day_profit_loss_percentage > 6):
            # There isn't an easy way to look at the whole month, need to keep a ledger
            return 0

        # buying power should account for orders, but check back later
        balance = accounts_data[0]['securitiesAccount']['currentBalances']['buyingPowerNonMarginableTrade']
        total_capital = accounts_data[0]['securitiesAccount']['currentBalances']['liquidationValue']
        return min(balance, total_capital * .02)

if __name__ == "__main__":
    moneymanager: MoneyManager = ConservativeMoneyManger()
    risk_capital = moneymanager.get_risk_capital()
    print(f"risk capital: {risk_capital}")