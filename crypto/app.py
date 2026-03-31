import requests

coins = input("Enter coins (comma separated e.g bitcoin,ethereum): ").lower()

url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=usd"

data = requests.get(url).json()

for coin, info in data.items():
    print(f"{coin.upper()} = ${info['usd']}")
