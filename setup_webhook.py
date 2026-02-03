import requests
from config import BOT_TOKEN

# Ваш Railway URL (той що ви бачите в Railway)
RAILWAY_URL = "https://sms-bot-production-4260.up.railway.app"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

print("=" * 50)
print("🚂 НАЛАШТУВАННЯ ВЕБХУКА ДЛЯ RAILWAY")
print("=" * 50)

print(f"🤖 Токен бота: {BOT_TOKEN}")
print(f"🌐 Railway URL: {RAILWAY_URL}")
print(f"🔗 Вебхук: {WEBHOOK_URL}")

# Спочатку перевіримо чи сервер працює
print("\n🔍 Перевіряємо сервер...")
try:
    health = requests.get(f"{RAILWAY_URL}/health", timeout=10)
    print(f"   Healthcheck статус: {health.status_code}")
    if health.status_code == 200:
        print("   ✅ Сервер працює!")
except:
    print("   ⚠️  Не вдалося досягти сервера, але пробуємо далі...")

# Встановлюємо вебхук
print("\n🔄 Встановлюємо вебхук в Telegram...")
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
    
    print(f"📊 Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok") and data.get("result"):
            print("✅ Вебхук успішно встановлено!")
            print(f"   📍 URL: {data['result'].get('url')}")
            print(f"   🔔 Оновлення: {data['result'].get('allowed_updates')}")
        else:
            print(f"⚠️  Telegram відповів: {data.get('description', 'Невідома помилка')}")
    else:
        print(f"❌ Помилка: {response.text}")
        
except Exception as e:
    print(f"🔥 Критична помилка: {str(e)}")
