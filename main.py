import requests
import os
import json
from datetime import datetime

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Add your games here (Steam AppIDs)
GAMES = {
    "Cities Skylines 2": "949230"
}

PRICE_FILE = "prices.json"

# ---------------- Helper Functions ----------------
def send_telegram_message(message):
    """Send a Telegram message."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_price(game_id):
    """Fetch current price from Steam API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={game_id}&cc=pl&filters=price_overview"
    response = requests.get(url)
    data = response.json()

    try:
        price_data = data[str(game_id)]["data"]["price_overview"]
        final_price = price_data["final"] / 100  # cents to PLN
        discount = price_data.get("discount_percent", 0)
        return final_price, discount
    except KeyError:
        return None, None

def load_previous_prices():
    """Load last saved prices from file."""
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_prices(prices):
    """Save updated prices to file."""
    with open(PRICE_FILE, "w") as f:
        json.dump(prices, f)

# ---------------- Main Function ----------------
def main():
    prices = load_previous_prices()
    new_prices = {}

    message_lines = [f"🕹 Steam Price Check ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"]

    for game_name, game_id in GAMES.items():
        price, discount = get_price(game_id)
        if price is None:
            message_lines.append(f"⚠ Could not fetch price for {game_name}")
            continue

        prev_price = prices.get(game_name)
        new_prices[game_name] = price

        if prev_price is None:
            message_lines.append(f"💾 Saved {game_name} price: {price} PLN")
        elif price < prev_price:
            message_lines.append(f"⬇ {game_name} dropped from {prev_price} PLN → {price} PLN (-{discount}%) 🎉")
        elif price > prev_price:
            message_lines.append(f"⬆ {game_name} increased from {prev_price} PLN → {price} PLN ❗")
        else:
            message_lines.append(f"🔁 {game_name}: no change ({price} PLN)")

    save_prices(new_prices)

    final_message = "\n".join(message_lines)
    print("---- Message content ----")
    print(final_message)
    print("--------------------------")

    try:
        send_telegram_message(final_message)
        print("✅ Telegram message sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

# ---------------- Run Script ----------------
if __name__ == "__main__":
    main()
# To run this script, ensure you have the required packages installed:
# pip install requests python-telegram-bot
# Set the BOT_TOKEN and CHAT_ID environment variables before running.