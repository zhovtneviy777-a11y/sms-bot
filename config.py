"""
config.py - Конфігурація веб-версії SMS Bot
"""

import os
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

# Налаштування веб-додатку
class Config:
    """Налаштування додатку"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", 8000))
    ENABLE_SELENIUM = os.getenv("ENABLE_SELENIUM", "false").lower() == "true"
    
    # Налаштування сесії
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 година

# Конфігурація сайтів
SITES_CONFIG = {
    "OLX.ua": {
        "name": "OLX.ua",
        "url": "https://www.olx.ua/uk/",
        "icon": "🛒",
        "category": "Оголошення",
        "description": "Платформа оголошень про продаж товарів та послуг",
        "enabled": True
    },
    "Rozetka.com.ua": {
        "name": "Rozetka.com.ua",
        "url": "https://rozetka.com.ua/",
        "icon": "💻",
        "category": "Магазин",
        "description": "Один з найбільших інтернет-магазинів електроніки в Україні",
        "enabled": True
    },
    "Prom.ua": {
        "name": "Prom.ua",
        "url": "https://prom.ua/",
        "icon": "📦",
        "category": "Маркетплейс",
        "description": "Торгова майданчик для бізнесу",
        "enabled": True
    },
    "NovaPoshta": {
        "name": "Нова Пошта",
        "url": "https://novaposhta.ua/",
        "icon": "🚚",
        "category": "Доставка",
        "description": "Служба доставки вантажів по Україні",
        "enabled": True
    },
    "EpicentrK.ua": {
        "name": "EpicentrK.ua",
        "url": "https://epicentrk.ua/",
        "icon": "🏠",
        "category": "Будівельний",
        "description": "Будівельний гіпермаркет",
        "enabled": True
    }
}

def check_config():
    """Перевірка конфігурації"""
    print("🔧 Конфігурація веб-версії SMS Bot")
    print(f"   Режим: {'Розробка' if Config.DEBUG else 'Виробництво'}")
    print(f"   Порт: {Config.PORT}")
    print(f"   Сайтів: {len(SITES_CONFIG)}")
    print(f"   Selenium: {'Активний' if Config.ENABLE_SELENIUM else 'Вимкнений'}")
    
    if Config.SECRET_KEY == "dev-secret-key-change-in-production":
        print("⚠️  Попередження: SECRET_KEY використовується за замовчуванням")
    
    if Config.ADMIN_PASSWORD == "admin123":
        print("⚠️  Попередження: ADMIN_PASSWORD за замовчуванням - змініть для безпеки")

# Автоматична перевірка
if __name__ == "__main__":
    check_config()
