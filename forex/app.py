import requests

# 1. Get inputs and clean them up (remove spaces)
base = input("Base currency (e.g USD): ").strip().upper()
raw_targets = input("Target currencies (comma separated, e.g NGN,EUR,GBP): ").strip().upper()

# 2. Split and clean individual target codes
targets = [t.strip() for t in raw_targets.split(',') if t.strip()]

# 3. Use the correct API parameters: 'base' and 'symbols'
url = f"https://api.frankfurter.app/latest?base={base}&symbols={','.join(targets)}"

try:
    response = requests.get(url)
    # The API often returns 422 for invalid currency codes
    if response.status_code == 422:
        print(f"❌ Error 422: One or more currency codes are invalid (e.g., '{base}' or '{targets}').")
    else:
        data = response.json()

        if "error" in data:
            print("❌ API Error:", data["error"])
        elif "rates" not in data:
            print("❌ No rates returned. Ensure codes are supported by ECB.")
        else:
            print(f"\n💱 Forex Rates (Base: {base}):")
            for cur, rate in data['rates'].items():
                print(f"1 {base} = {rate} {cur}")

except requests.exceptions.RequestException as e:
    print("❌ Network error:", e)
except ValueError:
    print("❌ Failed to parse response as JSON")
