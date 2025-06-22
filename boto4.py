import os
import requests
import time
from datetime import datetime
from telegram import Bot
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()
API_KEY        = os.getenv('BINANCE_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID        = os.getenv('TELEGRAM_CHAT_ID')

BASE    = 'https://api.binance.com'
HEADERS = {'X-MBX-APIKEY': API_KEY}
bot     = Bot(token=TELEGRAM_TOKEN)

# Множество для хранения уже отправленных соревнований
seen = set()

def fetch_competitions():
    resp = requests.get(f'{BASE}/sapi/v1/alpha/competitive/list', headers=HEADERS)
    resp.raise_for_status()
    now = int(datetime.utcnow().timestamp() * 1000)
    out = []
    for c in resp.json():
        if c['startTime'] <= now < c['endTime']:
            out.append({
                'id':     c.get('competitionId'),
                'name':   c.get('competitionName', c.get('competitionId')),
                'symbol': c['symbol'],
                'reward': c['rewardAmount'],
                'end':    datetime.fromtimestamp(c['endTime'] / 1000),
                'limit':  c.get('volumeLimit')
            })
    return out

def notify(text):
    bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

def check_and_notify():
    for comp in fetch_competitions():
        key = comp['id']
        if key not in seen:
            seen.add(key)
            message = (
                f"🏆 <b>New Competition Started</b>\n"
                f"<b>{comp['name']}</b> on <code>{comp['symbol']}</code>\n"
                f"🎁 Total Rewards: {comp['reward']}\n"
                f"📊 Volume ≥ {comp['limit']} USDT\n"
                f"⏳ Ends: {comp['end']:%Y-%m-%d %H:%M}"
            )
            notify(message)

if __name__ == '__main__':
    notify("🤖 Competition-bot started (monitoring Alpha competitions).")
    # Однократный запуск и выход
    check_and_notify()
