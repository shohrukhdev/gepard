import requests

BOT_TOKEN = "7579963454:AAHeUGjThsYobNytNQR334LrR3lh2R96DDk"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": 631751797,
        "text": text,
        "parse_mode": 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        print(f"Message send successfully: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

