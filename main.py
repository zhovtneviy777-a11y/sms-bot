from flask import Flask, jsonify, request
import threading
import time
import os
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Завантажуємо конфігурацію
from config import BOT_TOKEN, SITES_CONFIG

# Глобальний стан бота
bot_state = {
    "driver": None,
    "ready": False,
    "error": None,
    "started_at": time.time(),
    "last_activity": None
}

def init_selenium():
    """Ініціалізація Selenium з Docker-сумісними налаштуваннями"""
    try:
        logger.info("🤖 Запускаємо Selenium...")
        time.sleep(5)
        
        chrome_options = Options()
        
        # Docker-сумісні налаштування
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--window-size=1280,720")
        
        # Важливо для Docker
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Для Railway/Heroku
        chrome_options.binary_location = "/usr/bin/chromium"  # Шлях до Chrome у Docker
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Приховуємо автоматизацію
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        bot_state["driver"] = driver
        bot_state["ready"] = True
        bot_state["last_activity"] = time.time()
        
        logger.info("✅ Selenium готовий!")
        
        # Тестовий запит
        driver.get("https://www.google.com")
        logger.info(f"📄 Тестова сторінка: {driver.title}")
        
    except Exception as e:
        bot_state["error"] = str(e)
        logger.error(f"❌ Помилка ініціалізації Selenium: {e}")
        import traceback
        traceback.print_exc()

@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    if request.method == 'GET':
        return jsonify({
            "status": "ready",
            "bot": "Telegram Phone Bot",
            "endpoint": "/webhook"
        }), 200
    
    try:
        data = request.json
        if not data:
            return jsonify({"ok": True})
        
        logger.info("📨 Отримано повідомлення від Telegram")
        
        if 'message' in data and 'text' in data['message']:
            text = data['message']['text'].strip()
            chat_id = data['message']['chat']['id']
            
            if text == '/start':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "🤖 Привіт! Я бот для реєстрації номерів телефонів.\n\nКоманди:\n/status - статус\n/sites - сайти\n/help - допомога",
                    "parse_mode": "HTML"
                })
            
            elif text == '/status':
                status = "✅ Працює" if bot_state["ready"] else "⏳ Запускається"
                error_info = f"\n❌ Помилка: {bot_state['error']}" if bot_state["error"] else ""
                uptime = time.time() - bot_state["started_at"]
                
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"📊 Статус: {status}\n⏱️ Аптайм: {int(uptime)} сек\n🌐 Домен: sms-bot-production-4260.up.railway.app{error_info}",
                    "parse_mode": "HTML"
                })
            
            elif text == '/sites':
                sites = "\n".join([f"• {site}" for site in SITES_CONFIG.keys()])
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"🌐 Доступні сайти:\n\n{sites}",
                    "parse_mode": "HTML"
                })
            
            elif text == '/help':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❓ Допомога:\n\n/start - початок\n/status - статус\n/sites - сайти",
                    "parse_mode": "HTML"
                })
            
            else:
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❓ Невідома команда. Спробуйте /start",
                    "parse_mode": "HTML"
                })
    
    except Exception as e:
        logger.error(f"Помилка обробки вебхука: {e}")
    
    return jsonify({"ok": True})

@app.route('/health')
def health():
    if bot_state["ready"]:
        return jsonify({
            "status": "healthy", 
            "selenium": "ready",
            "uptime": time.time() - bot_state["started_at"]
        }), 200
    elif bot_state["error"]:
        return jsonify({
            "status": "error",
            "error": bot_state["error"]
        }), 500
    else:
        return jsonify({"status": "starting"}), 202

@app.route('/')
def home():
    return """<h1>🤖 Telegram Phone Bot</h1>
<p>Бот працює! Переходьте в Telegram: @my_1qop1_bot</p>
<p><a href="/health">Healthcheck</a></p>
<p><a href="/webhook">Webhook endpoint</a></p>"""

if __name__ == '__main__':
    # Запускаємо Selenium у окремому потоці
    selenium_thread = threading.Thread(target=init_selenium, daemon=True)
    selenium_thread.start()
    
    # Запускаємо Flask
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Сервер запущено на порті {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
