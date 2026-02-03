import requests
import os

# Токен прямо у файлі (тимчасово)
TOKEN = "8529982274:AAGIPNXQg7bkGKGEpUCpPNiSrT2NF3tPvns"
URL = "https://sms-bot-production-4260.up.railway.app/webhook"

print("🔄 Налаштування вебхука...")

# Проста перевірка
try:
    # Тест токена
    test = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe").json()
    if test.get("ok"):
        print(f"✅ Бот: @{test['result']['username']}")
    else:
        print(f"❌ Помилка: {test.get('description')}")
        exit(1)
    
    # Встановлення вебхука
    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/setWebhook",
        json={"url": URL, "drop_pending_updates": True}
    )
    
    if response.status_code == 200:
        print("✅ Вебхук встановлено!")
        print(response.json())
    else:
        print(f"❌ Помилка: {response.text}")
        
except Exception as e:
    print(f"❌ Помилка: {e}")
