import requests

symbol = input("Enter stock symbol (e.g AAPL, TSLA): ").lower()

url = f"https://stooq.com/q/l/?s={symbol}.us&f=sd2t2ohlcv&h&e=csv"

res = requests.get(url)

data = res.text.split("\n")[1].split(",")

if data and data[0] != "N/D":
    print(f"\n📊 {symbol.upper()} Stock Data")
    print("Date:", data[1])
    print("Open:", data[3])
    print("High:", data[4])
    print("Low:", data[5])
    print("Close:", data[6])
    print("Volume:", data[7])
else:
    print("❌ Invalid symbol or no data")
