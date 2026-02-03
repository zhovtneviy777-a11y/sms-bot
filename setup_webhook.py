import requests
from config import BOT_TOKEN
import os

# Отримуємо URL з змінних середовища або використовуємо за замовчуванням
RAILWAY_URL = "https://sms-bot-production-4260.up.railway.app"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

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
