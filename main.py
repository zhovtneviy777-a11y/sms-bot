from flask import Flask, jsonify, request
import threading
import time
import os
import logging
import json
import requests  # Додаємо requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Завантажуємо конфігурацію з .env
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ ПОМИЛКА: BOT_TOKEN не знайдено в .env файлі!")
    exit(1)

SITES_CONFIG = {
    "OLX.ua": {
        "url": "https://www.olx.ua/uk/",
        "phone_selectors": ["input[type='tel']", "input[name*='phone']"],
        "submit_selectors": ["button[type='submit']"],
        "timeout": 10
    }
}

bot_state = {
    "ready": True,
    "started_at": time.time(),
    "last_activity": None
}

def send_telegram_message(chat_id, text):
    """Надсилає повідомлення через Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Помилка відправки повідомлення: {e}")
        return None

@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    if request.method == 'GET':
        return jsonify({
            "status": "ready",
            "bot": "Telegram Phone Bot",
            "token_valid": BOT_TOKEN[:10] + "..."
        }), 200
    
    try:
        data = request.json
        if not data:
            return jsonify({"ok": True})
        
        logger.info(f"📨 Отримано дані: {json.dumps(data)[:200]}...")
        
        if 'message' in data and 'text' in data['message']:
            text = data['message']['text'].strip()
            chat_id = data['message']['chat']['id']
            
            if text == '/start':
                response_text = "🤖 Привіт! Я бот для реєстрації номерів телефонів.\n\nКоманди:\n/status - статус\n/sites - сайти\n/help - допомога"
            elif text == '/status':
                response_text = f"📊 Статус: ✅ Працює\n🌐 Домен: sms-bot-production-4260.up.railway.app\n⏱️ Аптайм: {int(time.time() - bot_state['started_at'])} сек"
            elif text == '/sites':
                sites = "\n".join([f"• {site}" for site in SITES_CONFIG.keys()])
                response_text = f"🌐 Доступні сайти:\n\n{sites}"
            elif text == '/help':
                response_text = "❓ Допомога:\n\n/start - початок\n/status - статус\n/sites - сайти"
            else:
                response_text = "❓ Невідома команда. Спробуйте /start"
            
            # Надсилаємо відповідь через Telegram API
            send_telegram_message(chat_id, response_text)
            
            return jsonify({"ok": True})
    
    except Exception as e:
        logger.error(f"Помилка обробки вебхука: {e}")
    
    return jsonify({"ok": True})

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "telegram_token": "valid" if BOT_TOKEN else "invalid",
        "uptime": time.time() - bot_state["started_at"]
    }), 200

@app.route('/')
def home():
    return """<h1>🤖 Telegram Phone Bot</h1>
<p>Бот працює! Переходьте в Telegram.</p>
<p><a href="/health">Healthcheck</a></p>"""

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Сервер запущено на порті {port}")
    logger.info(f"🤖 Токен бота: {BOT_TOKEN[:10]}...")
    app.run(host='0.0.0.0', port=port, debug=False)
