import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ПОМИЛКА: BOT_TOKEN не знайдено!")
    exit(1)

print(f"✅ Config завантажено. Бот: {BOT_TOKEN[:10]}...")

SITES_CONFIG = {
    "OLX.ua": {
        "url": "https://www.olx.ua/uk/",
        "phone_selectors": ["input[type='tel']", "input[name*='phone']"],
        "submit_selectors": ["button[type='submit']"],
        "timeout": 10
    },
    "Rozetka.com.ua": {
        "url": "https://rozetka.com.ua/",
        "phone_selectors": ["input[type='tel']", "#auth_email"],
        "submit_selectors": ["button[type='submit']"],
        "timeout": 10
    },
    "Prom.ua": {
        "url": "https://prom.ua/",
        "phone_selectors": ["input[type='tel']", "input[name*='phone']"],
        "submit_selectors": ["button[type='submit']"],
        "timeout": 10
    }
}
