import requests
import os
import sys
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

# Отримуємо токен з .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ ПОМИЛКА: BOT_TOKEN не встановлено!")
    print("Створіть файл .env з BOT_TOKEN=ваш_токен")
    sys.exit(1)

RAILWAY_URL = "https://sms-bot-production-4260.up.railway.app"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

print("=" * 60)
print("🚂 НАЛАШТУВАННЯ TELEGRAM ВЕБХУКА")
print("=" * 60)

print(f"🤖 Токен: {BOT_TOKEN[:15]}...")
print(f"🌐 Railway URL: {RAILWAY_URL}")
print(f"🔗 Вебхук: {WEBHOOK_URL}")

# 1. Перевірка токена
print("\n🔍 Перевіряємо токен бота...")
try:
    bot_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
    bot_data = bot_response.json()
    
    if bot_response.status_code == 200 and bot_data.get("ok"):
        bot_info = bot_data["result"]
        print(f"✅ Бот знайдено!")
        print(f"   👤 Ім'я: {bot_info.get('first_name')}")
        print(f"   📛 Username: @{bot_info.get('username')}")
        print(f"   🆔 ID: {bot_info.get('id')}")
    else:
        print(f"❌ Помилка токена: {bot_data.get('description')}")
        print(f"   Статус: {bot_response.status_code}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Помилка перевірки токена: {str(e)}")
    sys.exit(1)

# 2. Перевірка Railway
print("\n🔍 Перевіряємо Railway сервер...")
try:
    health_response = requests.get(f"{RAILWAY_URL}/health", timeout=15)
    if health_response.status_code == 200:
        print(f"✅ Сервер працює (статус: {health_response.status_code})")
        print(f"   Відповідь: {health_response.json()}")
    else:
        print(f"⚠️  Сервер відповідає {health_response.status_code}")
        print(f"   Відповідь: {health_response.text[:100]}")
except Exception as e:
    print(f"⚠️  Не вдалося перевірити сервер: {e}")
    print("   Продовжуємо налаштування вебхука...")

# 3. Встановлення вебхука
print("\n🔄 Встановлюємо Telegram вебхук...")
try:
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={
            "url": WEBHOOK_URL,
            "drop_pending_updates": True,
            "allowed_updates": ["message", "callback_query"],
            "max_connections": 40
        },
        timeout=30
    )
    
    print(f"📊 HTTP Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("✅ Вебхук успішно встановлено!")
            print(f"   🔗 URL: {data['result'].get('url')}")
            
            # Перевірка налаштувань
            print("\n🔍 Перевіряємо налаштування вебхука...")
            info_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
            if info_response.status_code == 200:
                info = info_response.json()
                if info.get("ok"):
                    webhook_info = info["result"]
                    print(f"   ✅ Поточний вебхук: {webhook_info.get('url')}")
                    print(f"   📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
        else:
            print(f"❌ Telegram повідомив помилку: {data.get('description')}")
    else:
        print(f"❌ HTTP помилка: {response.text}")
        
except Exception as e:
    print(f"❌ Помилка: {str(e)}")

print("\n" + "=" * 60)
print("📱 ЩО РОБИТИ ДАЛІ:")
print("1. Відкрийте Telegram")
print("2. Знайдіть @my_1qop1_bot")
print("3. Надішліть /start")
print("4. Перевірте логи в Railway")
print("=" * 60)
