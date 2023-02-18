from constants import TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH
from tda import auth, client
import json


try:
    tda_client = auth.client_from_token_file(TDA_TOKEN_PATH, TDA_API_KEY)
except FileNotFoundError:
    # go through the oauth2 workflow manually, but with a little help
    tda_client = auth.client_from_manual_flow(TDA_API_KEY, TDA_REDIRECT_URI, TDA_TOKEN_PATH)

response = tda_client.get_accounts()
assert response.status_code == 200, response.raise_for_status()
# print(json.dumps(response.json(), indent=4))

accounts = response.json()
balance = accounts[0]['securitiesAccount']['currentBalances']['cashBalance']
print(balance)
print('...see below')
print(json.dumps(accounts, indent=4))
