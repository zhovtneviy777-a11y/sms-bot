from flask import Flask, jsonify, request
import threading
import time
import os
import logging
from config import BOT_TOKEN, SITES_CONFIG

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Статуси бота
bot_status = {
    "driver": None,
    "ready": False,
    "error": None,
    "started_at": time.time()
}

def init_selenium():
    """Ініціалізація Selenium для бота"""
    global bot_status
    
    try:
        logger.info("🤖 Запускаємо Selenium...")
        time.sleep(10)  # Чекаємо на системні залежності
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        driver = webdriver.Chrome(options=chrome_options)
        bot_status["driver"] = driver
        bot_status["ready"] = True
        
        logger.info("✅ Selenium готовий!")
        
    except Exception as e:
        bot_status["error"] = str(e)
        logger.error(f"❌ Помилка: {e}")

@app.route('/health')
def health():
    """Healthcheck для Railway/Render"""
    if bot_status["ready"]:
        return jsonify({"status": "ready", "uptime": time.time() - bot_status["started_at"]}), 200
    elif bot_status["error"]:
        return jsonify({"status": "error", "error": bot_status["error"]}), 500
    else:
        return jsonify({"status": "starting"}), 202

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Обробка повідомлень від Telegram"""
    data = request.json
    logger.info(f"📨 Отримано: {data}")
    
    # Обробка команд
    if 'message' in data and 'text' in data['message']:
        text = data['message']['text']
        chat_id = data['message']['chat']['id']
        
        if text == '/start':
            return jsonify({
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "🤖 Бот для реєстрації номерів готовий до роботи!\n\nКоманди:\n/register - реєстрація номера\n/status - статус бота\n/sites - доступні сайти"
            })
        
        elif text == '/status':
            status_text = "✅ Готовий" if bot_status["ready"] else "⏳ Запускається..."
            return jsonify({
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": f"Статус бота: {status_text}"
            })
    
    return jsonify({"ok": True})

@app.route('/register', methods=['POST'])
def register_phone():
    """API для реєстрації номерів"""
    if not bot_status["ready"]:
        return jsonify({"error": "Бот не готовий"}), 503
    
    data = request.json
    phone = data.get('phone')
    site_name = data.get('site', 'OLX.ua')
    
    if not phone:
        return jsonify({"error": "Вкажіть номер телефону"}), 400
    
    try:
        # Використовуємо конфігурацію сайту
        site_config = SITES_CONFIG.get(site_name)
        if not site_config:
            return jsonify({"error": f"Сайт {site_name} не знайдено"}), 400
        
        driver = bot_status["driver"]
        from utils import safe_get, wait_for_element
        
        # Відкриваємо сайт
        safe_get(driver, site_config["url"])
        
        # Шукаємо поле для телефону
        phone_field = None
        for selector in site_config["phone_selectors"]:
            try:
                phone_field = driver.find_element_by_css_selector(selector)
                break
            except:
                continue
        
        if not phone_field:
            return jsonify({"error": "Не знайдено поле для телефону"}), 400
        
        # Вводимо номер
        phone_field.clear()
        phone_field.send_keys(phone)
        
        return jsonify({
            "success": True,
            "message": f"Номер {phone} введено на {site_name}",
            "site": site_name,
            "phone": phone
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sites')
def list_sites():
    """Список доступних сайтів"""
    sites = list(SITES_CONFIG.keys())
    return jsonify({"sites": sites})

# Запускаємо Selenium у фоні
threading.Thread(target=init_selenium, daemon=True).start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Запуск бота на порту {port}")
    logger.info(f"🤖 Токен бота: {'встановлено' if BOT_TOKEN else 'НЕ встановлено!'}")
    app.run(host='0.0.0.0', port=port, debug=False)
