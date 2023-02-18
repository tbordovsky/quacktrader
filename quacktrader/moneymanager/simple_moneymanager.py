from quacktrader.constants import TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH
from tda import auth, client
import json

from quacktrader.moneymanager.moneymanager import MoneyManager

try:
    tda_client = auth.client_from_token_file(TDA_TOKEN_PATH, TDA_API_KEY)
except FileNotFoundError:
    # go through the oauth2 workflow manually, but with a little help
    tda_client = auth.client_from_manual_flow(TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH)

class SimpleMoneyManger(MoneyManager):
    """Manage investment capital based on simple account balance"""

    def get_risk_capital(self) -> int:
        """Only allow cash-secured positions"""
        response = tda_client.get_accounts()
        assert response.status_code == 200, response.raise_for_status()
        # print(json.dumps(response.json(), indent=4))

        accounts = response.json()
        balance = accounts[0]['securitiesAccount']['currentBalances']['buyingPowerNonMarginableTrade']
        return balance

if __name__ == "__main__":
    moneymanager: MoneyManager = SimpleMoneyManger()
    risk_capital = moneymanager.get_risk_capital()
    print(f"risk capital: {risk_capital}")