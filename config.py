import os
from dotenv import load_dotenv

load_dotenv()  # Завантажує змінні з .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("⚠️  УВАГА: BOT_TOKEN не знайдено в .env файлі!")
    # АБО вставте токен прямо тут:
    # BOT_TOKEN = "ВАШ_ТОКЕН_ТУТ"
