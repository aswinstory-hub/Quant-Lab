from kiteconnect import KiteConnect

api_key = "74rj48jkshla0dgo"
api_secret = "YOUR_API_SECRET"   # from app page
request_token = "PASTE_HERE"

kite = KiteConnect(api_key=api_key)

data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]

print(access_token)
