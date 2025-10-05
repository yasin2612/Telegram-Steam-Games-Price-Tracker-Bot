import requests
import os
import json
from datetime import datetime

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PRICE_FILE = "prices.json"
GAMES_FILE = "games.json"

# ---------------- Helper Functions ----------------

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def load_previous_prices():
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_prices(prices):
    with open(PRICE_FILE, "w") as f:
        json.dump(prices, f)

def load_games():
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_games(games):
    with open(GAMES_FILE, "w") as f:
        json.dump(games, f)

# ---------------- Steam Price Fetcher ----------------

def get_price(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=pl&filters=price_overview"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Sometimes API returns empty dict or unexpected structure
        if not data or str(app_id) not in data:
            return None, None

        app_data = data[str(app_id)]
        if not app_data.get("success", False):
            return None, None

        price_info = app_data.get("data", {}).get("price_overview")
        if not price_info:
            return None, None

        final_price = price_info["final"] / 100  # cents to PLN
        discount = price_info.get("discount_percent", 0)
        return final_price, discount

    except Exception as e:
        print(f"❌ Error fetching price for AppID {app_id}: {e}")
        return None, None


# ---------------- Telegram Command Handler ----------------

def handle_telegram_commands():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1"
    response = requests.get(url).json()
    
    if "result" not in response or not response["result"]:
        return
    
    last_item = response["result"][-1]
    
    # Check if "message" exists
    if "message" not in last_item:
        return
    
    if "text" not in last_item["message"]:
        return
    
    last_message = last_item["message"]["text"]

    games = load_games()
    message_to_send = ""

    if last_message.startswith("/add"):
        try:
            _, name, app_id, threshold = last_message.split(" ", 3)
            games[name] = {"app_id": app_id, "threshold": float(threshold)}
            save_games(games)
            message_to_send = f"✅ Added {name} with threshold {threshold} PLN"
        except Exception:
            message_to_send = "❌ Usage: /add <Game Name> <AppID> <Threshold>"

    elif last_message.startswith("/remove"):
        try:
            _, name = last_message.split(" ", 1)
            if name in games:
                del games[name]
                save_games(games)
                message_to_send = f"✅ Removed {name}"
            else:
                message_to_send = f"⚠ {name} not found"
        except Exception:
            message_to_send = "❌ Usage: /remove <Game Name>"

    elif last_message.startswith("/list"):
        if games:
            lines = [f"{g}: AppID={games[g]['app_id']}, Threshold={games[g]['threshold']} PLN" for g in games]
            message_to_send = "🎮 Tracked Games:\n" + "\n".join(lines)
        else:
            message_to_send = "⚠ No games tracked yet."

    if message_to_send:
        send_telegram_message(message_to_send)


# ---------------- Price Check ----------------

def check_prices():
    games = load_games()
    if not games:
        send_telegram_message("⚠ No games to track.")
        return

    prices = load_previous_prices()
    new_prices = {}
    message_lines = [f"🕹 Steam Price Check ({datetime.now().strftime('%Y-%m-%d %H:%M')})"]

    for game_name, game_info in games.items():
        app_id = game_info["app_id"]
        threshold = game_info.get("threshold", 0)

        price, discount = get_price(app_id)
        if price is None:
            message_lines.append(f"⚠ Could not fetch price for {game_name}")
            continue

        prev_price = prices.get(game_name)
        new_prices[game_name] = price

        if prev_price is None:
            message_lines.append(f"💾 Saved {game_name} price: {price} PLN")
        elif price < prev_price and price <= threshold:
            message_lines.append(f"⬇ {game_name} dropped from {prev_price} → {price} PLN (-{discount}%) 🎉")
        elif price > prev_price:
            message_lines.append(f"⬆ {game_name} increased from {prev_price} → {price} PLN ❗")
        else:
            message_lines.append(f"🔁 {game_name}: no change ({price} PLN)")

    save_prices(new_prices)
    final_message = "\n".join(message_lines)
    send_telegram_message(final_message)

# ---------------- Run Script ----------------

if __name__ == "__main__":
    handle_telegram_commands()  # Process any commands sent via Telegram
    check_prices()              # Check prices and send alerts

# To run this script, ensure you have the required packages installed:
# pip install requests python-telegram-bot
# Set the BOT_TOKEN and CHAT_ID environment variables before running.