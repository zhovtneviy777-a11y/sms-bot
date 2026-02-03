import requests
from config import BOT_TOKEN
import os

# Отримуємо URL з змінних середовища або використовуємо за замовчуванням
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ваш-додаток.onrender.com/webhook")

print("🔄 Налаштування вебхука для Telegram...")
print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
print(f"🌐 URL: {WEBHOOK_URL}")

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "drop_pending_updates": True,
        "allowed_updates": ["message"]
    }
)

print(f"📊 Статус: {response.status_code}")
print(f"📄 Відповідь: {response.json()}")
