import os
import requests
from datetime import datetime
from telegram import Bot
from dotenv import load_dotenv

# ── 1. Загружаем переменные окружения ──────────────────────────────────────────
load_dotenv()                        # .env локально или Secrets на GitHub

API_KEY        = os.getenv("BINANCE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://api.binance.com"
HEADERS  = {"X-MBX-APIKEY": API_KEY}

bot   = Bot(token=TELEGRAM_TOKEN)
seen  = set()                        # хранит ID соревнований в рамках ОДНОГО запуска


# ── 2. Функция запроса Competition ────────────────────────────────────────────
def fetch_competitions() -> list[dict]:
    """Возвращает список активных Alpha-соревнований."""
    resp = requests.get(f"{BASE_URL}/sapi/v1/alpha/competitive/list",
                        headers=HEADERS, timeout=10)
    resp.raise_for_status()

    now_ms = int(datetime.utcnow().timestamp() * 1000)
    comps  = []
    for c in resp.json():
        if c["startTime"] <= now_ms < c["endTime"]:
            comps.append({
                "id":     c.get("competitionId"),
                "name":   c.get("competitionName", c["competitionId"]),
                "symbol": c["symbol"],
                "reward": c["rewardAmount"],
                "end":    datetime.fromtimestamp(c["endTime"] / 1000),
                "limit":  c.get("volumeLimit", "N/A")
            })
    return comps


# ── 3. Отправка уведомления ───────────────────────────────────────────────────
def notify(msg: str) -> None:
    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")


# ── 4. Основная логика ────────────────────────────────────────────────────────
def main() -> None:
    new = 0
    for comp in fetch_competitions():
        if comp["id"] not in seen:
            seen.add(comp["id"])
            new += 1
            message = (
                f"🏆 <b>New Alpha Competition</b>\n"
                f"<b>{comp['name']}</b>  on  <code>{comp['symbol']}</code>\n"
                f"🎁 Rewards: {comp['reward']}\n"
                f"📊 Volume ≥ {comp['limit']} USDT\n"
                f"⏳ Ends: {comp['end']:%Y-%m-%d %H:%M UTC}"
            )
            notify(message)

    if new == 0:
        print("No new competitions found.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        notify(f"⚠️ Bot error: {e}")
        raise
        
