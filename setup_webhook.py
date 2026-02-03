import requests
import os
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ ПОМИЛКА: BOT_TOKEN не знайдено в .env файлі!")
    print("Додайте BOT_TOKEN=ваш_токен у .env файл")
    exit(1)

URL = "https://sms-bot-production-4260.up.railway.app/webhook"

print("🔄 Налаштування вебхука...")
print(f"URL: {URL}")
print(f"Токен: {TOKEN[:10]}...")  # Показуємо тільки перші 10 символів

# Проста перевірка
try:
    # Тест токена
    print("🔍 Перевірка токена бота...")
    test = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=10).json()
    
    if test.get("ok"):
        print(f"✅ Бот: @{test['result']['username']}")
        print(f"📝 ID: {test['result']['id']}")
        print(f"👤 Ім'я: {test['result']['first_name']}")
    else:
        print(f"❌ Помилка: {test.get('description')}")
        exit(1)
    
    # Отримуємо поточний вебхук
    print("🔍 Перевірка поточного вебхука...")
    current = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
    
    if current.get("ok") and current["result"]["url"]:
        print(f"📌 Поточний вебхук: {current['result']['url']}")
    
    # Встановлення вебхука
    print("⚙️ Встановлення нового вебхука...")
    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/setWebhook",
        json={
            "url": URL,
            "drop_pending_updates": True,
            "max_connections": 100
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("✅ Вебхук успішно встановлено!")
            print(f"📊 Результат: {result.get('description', 'OK')}")
            
            # Повторна перевірка
            verify = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
            if verify.get("ok"):
                print(f"🔐 Підтверджено: {verify['result']['url']}")
                print(f"📈 Очікуючих оновлень: {verify['result']['pending_update_count']}")
        else:
            print(f"❌ Помилка API: {result.get('description')}")
    else:
        print(f"❌ HTTP помилка: {response.status_code}")
        print(f"📄 Відповідь: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Таймаут запиту! Перевірте підключення до інтернету")
except requests.exceptions.ConnectionError:
    print("❌ Помилка підключення! Перевірте мережу")
except Exception as e:
    print(f"❌ Неочікувана помилка: {e}")
    import traceback
    traceback.print_exc()

print("\n📝 Інструкції:")
print("1. Перейдіть у свого бота в Telegram")
print("2. Надішліть команду /start")
print("3. Перевірте статус командою /status")
