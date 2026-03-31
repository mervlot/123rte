import requests

url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"

data = requests.get(url).json()

for coin in data[:5]:
    print(coin["name"])
    print("Price:", coin["current_price"])
    print("Market Cap:", coin["market_cap"])
    print("-" * 30)
