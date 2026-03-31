import requests

# --- Metals ---
metals_url = "https://api.metals.live/v1/spot"
metals = requests.get(metals_url).json()

gold = next((i["gold"] for i in metals if "gold" in i), None)
silver = next((i["silver"] for i in metals if "silver" in i), None)

# --- Oil ---
oil_url = "https://stooq.com/q/l/?s=cl.f&f=sd2t2ohlcv&h&e=csv"
oil_res = requests.get(oil_url)
oil_data = oil_res.text.split("\n")[1].split(",")

print("\n🛢️ Commodities Dashboard")

print(f"Gold: {gold}")
print(f"Silver: {silver}")
print(f"Oil Close: {oil_data[6]}")
