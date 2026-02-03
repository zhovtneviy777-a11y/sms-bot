import requests
from config import BOT_TOKEN

# Ваш Railway URL (згідно зі скріншотом)
RAILWAY_URL = "https://sms-bot-production-4260.up.railway.app"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

print("=" * 60)
print("🚂 НАЛАШТУВАННЯ ВЕБХУКА TELEGRAM ДЛЯ RAILWAY")
print("=" * 60)

print(f"🤖 Токен бота: {BOT_TOKEN}")
print(f"🌐 Railway домен: {RAILWAY_URL}")
print(f"🔗 Вебхук URL: {WEBHOOK_URL}")

# 1. Перевіряємо чи працює сервер
print("\n🔍 Перевіряємо сервер...")
try:
    response = requests.get(f"{RAILWAY_URL}/health", timeout=15)
    print(f"   Healthcheck: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Сервер працює нормально!")
    else:
        print(f"   ⚠️  Сервер відповідає {response.status_code}")
        print(f"   Відповідь: {response.text[:100]}")
except Exception as e:
    print(f"   ❌ Помилка підключення: {e}")

# 2. Перевіряємо поточний вебхук
print("\n📊 Перевіряємо поточний вебхук...")
try:
    info_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo", timeout=10)
    if info_response.status_code == 200:
        info = info_response.json()
        if info.get("ok") and info.get("result", {}).get("url"):
            current_url = info["result"]["url"]
            print(f"   Поточний вебхук: {current_url}")
            if current_url == WEBHOOK_URL:
                print("   ✅ Вебхук вже налаштовано!")
            else:
                print("   ⚠️  Вебхук вказує на інший URL")
except Exception as e:
    print(f"   ❌ Не вдалося перевірити вебхук: {e}")

# 3. Встановлюємо новий вебхук
print("\n🔄 Встановлюємо вебхук...")
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
    
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok") and data.get("result"):
            print("   ✅ Вебхук успішно встановлено!")
            print(f"   🔗 URL: {data['result'].get('url')}")
            print(f"   📋 Оновлення: {data['result'].get('allowed_updates')}")
            
            # Перевіряємо знову
            print("\n🔍 Підтвердження...")
            info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo").json()
            if info.get("ok"):
                print(f"   ✅ Підтверджено: {info['result'].get('url')}")
                print(f"   ✅ Очікуючих оновлень: {info['result'].get('pending_update_count', 0)}")
        else:
            print(f"   ❌ Telegram повідомляє: {data.get('description', 'Невідома помилка')}")
    else:
        print(f"   ❌ HTTP помилка: {response.text}")
        
except Exception as e:
    print(f"   🔥 Критична помилка: {str(e)}")

print("\n" + "=" * 60)
print("📱 Щоб протестувати бота:")
print("1. Відкрийте Telegram")
print("2. Знайдіть вашого бота")
print("3. Надішліть /start")
print("4. Перевірте логи в Railway")
print("=" * 60)
