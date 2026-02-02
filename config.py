# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота (отримайте у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Конфігурація сайтів
SITES_CONFIG = {
    "OLX.ua": {
        "url": "https://www.olx.ua/uk/",
        "phone_selectors": [
            "input[type='tel']",
            "input[type='phone']",
            "input[name*='phone']",
            "input[id*='phone']",
            "input[name*='Phone']",
            "input[name*='telephone']"
        ],
        "submit_selectors": [
            "button[type='submit']",
            "input[type='submit']",
            ".submit",
            ".login-button",
            ".btn-primary"
        ],
        "timeout": 10
    },
    "Rozetka.com.ua": {
        "url": "https://rozetka.com.ua/",
        "phone_selectors": [
            "input[type='tel']",
            "input[type='phone']",
            "#auth_email",
            ".auth-input"
        ],
        "submit_selectors": [
            "button[type='submit']",
            ".auth-submit",
            ".button.button_color_green"
        ],
        "timeout": 10
    },
    "Prom.ua": {
        "url": "https://prom.ua/",
        "phone_selectors": [
            "input[type='tel']",
            "input[name*='phone']",
            "#phone"
        ],
        "submit_selectors": [
            "button[type='submit']",
            ".js-submit-button"
        ],
        "timeout": 10
    },
    "NovaPoshta": {
        "url": "https://novaposhta.ua/",
        "phone_selectors": [
            "input[type='tel']",
            "input[name*='phone']",
            "#recipientPhone"
        ],
        "submit_selectors": [
            "button[type='submit']",
            ".button.primary"
        ],
        "timeout": 15
    },
    "EpicentrK.ua": {
        "url": "https://epicentrk.ua/",
        "phone_selectors": [
            "input[type='tel']",
            "input[name*='phone']",
            ".auth-phone-input"
        ],
        "submit_selectors": [
            "button[type='submit']",
            ".auth-submit"
        ],
        "timeout": 10
    }
}

# Налаштування Selenium
SELENIUM_CONFIG = {
    "headless": True,
    "window_size": "1920,1080",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "timeout": 30
}

# Налаштування логування
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "bot.log"
}
