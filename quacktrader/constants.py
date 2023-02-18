import os


TDA_TOKEN_PATH = os.getenv('TDA_TOKEN_PATH', '/tmp/tda-access-token.json')
TDA_API_KEY = os.getenv('TDA_API_KEY') # make sure to include the postfix '@AMER.OAUTHAP'
TDA_REDIRECT_URI = os.getenv('TDA_REDIRECT_URI')