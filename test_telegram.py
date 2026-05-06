import json
import urllib.request
import os

TELEGRAM_BOT_TOKEN = "8681386306:AAH-4byV0iBf-M7btDkNe7tQ4lkd1GXmGRU"
TELEGRAM_CHAT_ID = "8385047011"

def send_telegram_message(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing config")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method="POST")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req)
        print("Success")
    except Exception as e:
        print(f"Telegram Error: {e}")

send_telegram_message("Test message")
