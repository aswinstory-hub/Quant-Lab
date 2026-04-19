from kiteconnect import KiteConnect 

api_key = input(str("Enter API Key: "))

kite = KiteConnect(api_key=api_key)

print(kite.login_url())

print("=========================================")

request_token = input(str("Enter Request Token: "))
api_secret = input(str("Enter API Secret Key: "))

data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]

print(access_token)
