import requests
import json
import os
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = "8304783436:AAG_VcV_uUqSrHOptuMxOBrmkPAIgJ0RGWU" #Replace with your bot token
CHAT_ID = "1786275869" #Replace with your chat ID
COUNTRY = "PL"  # Poland
GAMES = {
    949230: "Cities Skylines 2",
    1174180: "Red Dead Redemption 2"
    # You can add more later, e.g.
    # 730: "Counter-Strike 2",
    # 1174180: "Red Dead Redemption 2"
}
DATA_FILE = "prices.json"


# === FUNCTIONS ===
def get_price(app_id, country=COUNTRY):
    """Fetch current price (in PLN) from Steam API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc={country}&filters=price_overview"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()[str(app_id)]
        if data.get("success") and "price_overview" in data["data"]:
            return data["data"]["price_overview"]["final"] / 100
    except Exception as e:
        print(f"Error fetching price for {app_id}: {e}")
    return None


def send_telegram(message):
    """Send Telegram message."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})


def load_prices():
    """Load saved prices from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_prices(data):
    """Save prices to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    saved_prices = load_prices()
    updated_prices = saved_prices.copy()

    for app_id, name in GAMES.items():
        current_price = get_price(app_id)
        if current_price is None:
            print(f"⚠️ Could not fetch price for {name}")
            continue

        previous_price = saved_prices.get(str(app_id))
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if previous_price is None:
            # First-time setup
            print(f"Added {name} to tracking: {current_price} PLN")
            updated_prices[str(app_id)] = current_price
            send_telegram(f"🆕 Tracking started for {name}\nCurrent price: {current_price} PLN")
        elif current_price < previous_price:
            print(f"🔻 Price drop detected for {name}: {previous_price} → {current_price}")
            send_telegram(f"💸 Price drop!\n{name}: {previous_price} → {current_price} PLN\nTime: {now}")
            updated_prices[str(app_id)] = current_price
        elif current_price > previous_price:
            print(f"⬆️ Price increased for {name}: {previous_price} → {current_price}")
            updated_prices[str(app_id)] = current_price
        else:
            print(f"✅ {name} unchanged: {current_price} PLN")

    save_prices(updated_prices)
    print("✅ Prices saved.")


if __name__ == "__main__":
    main()
