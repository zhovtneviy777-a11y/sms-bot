import requests
import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

# Отримуємо токен з .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ ПОМИЛКА: BOT_TOKEN не встановлено!")
    print("Створіть файл .env з BOT_TOKEN=ваш_токен")
    exit(1)

RAILWAY_URL = "https://sms-bot-production-4260.up.railway.app"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

print("=" * 60)
print(f"🤖 Токен: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
print(f"🌐 Вебхук: {WEBHOOK_URL}")

# Тестуємо токен
print("\n🔍 Перевіряємо токен...")
test = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()
if test.get("ok"):
    print(f"✅ Бот: @{test['result']['username']}")
else:
    print(f"❌ Помилка токена: {test.get('description')}")
    exit(1)

# Встановлюємо вебхук
print("\n🔄 Встановлюємо вебхук...")
response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "drop_pending_updates": True
    }
)

print(f"📊 Статус: {response.status_code}")
print(f"📄 Відповідь: {response.json()}")
