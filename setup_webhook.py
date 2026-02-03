import requests
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAILWAY_URL = "https://sms-bot-production-4260.up.railway.app"

print("🔍 ДЕТАЛЬНА ПЕРЕВІРКА СИСТЕМИ")
print("=" * 50)

# 1. Перевірка .env
print("\n1. Перевірка .env файлу...")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не знайдено!")
else:
    print(f"✅ Токен: {BOT_TOKEN[:15]}...")

# 2. Перевірка Railway
print("\n2. Перевірка Railway сервера...")
try:
    health = requests.get(f"{RAILWAY_URL}/health", timeout=10)
    print(f"✅ Healthcheck: {health.status_code}")
    if health.status_code == 200:
        print(f"   Відповідь: {health.json()}")
except:
    print("❌ Не вдалося досягти Railway")

# 3. Перевірка Telegram бота
print("\n3. Перевірка Telegram бота...")
try:
    bot_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()
    if bot_info.get("ok"):
        print(f"✅ Бот: @{bot_info['result']['username']}")
    else:
        print(f"❌ Помилка: {bot_info.get('description')}")
except:
    print("❌ Помилка підключення до Telegram")

# 4. Перевірка вебхука
print("\n4. Перевірка вебхука...")
try:
    webhook_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo").json()
    if webhook_info.get("ok"):
        result = webhook_info["result"]
        print(f"✅ Вебхук URL: {result.get('url', 'Не встановлено')}")
        print(f"   Pending updates: {result.get('pending_update_count', 0)}")
        print(f"   Last error: {result.get('last_error_message', 'Немає')}")
    else:
        print(f"❌ Помилка: {webhook_info.get('description')}")
except:
    print("❌ Не вдалося перевірити вебхук")

print("\n" + "=" * 50)
print("✅ Перевірка завершена!")
