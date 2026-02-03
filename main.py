from flask import Flask, jsonify, request
import threading
import time
import os
import logging
import json
from config import BOT_TOKEN, SITES_CONFIG

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальний стан бота
bot_state = {
    "driver": None,
    "ready": False,
    "error": None,
    "started_at": time.time(),
    "processing": False,
    "last_activity": None
}

def init_selenium():
    """Ініціалізація Selenium"""
    try:
        logger.info("🤖 Запускаємо Selenium...")
        time.sleep(5)
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        bot_state["driver"] = driver
        bot_state["ready"] = True
        bot_state["last_activity"] = time.time()
        
        logger.info("✅ Selenium готовий до роботи!")
        
    except Exception as e:
        bot_state["error"] = str(e)
        logger.error(f"❌ Помилка Selenium: {e}")

# ========== TELEGRAM WEBHOOK HANDLER ==========

@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    """Обробка вебхука від Telegram"""
    
    # Обробка GET запиту (перевірка роботи)
    if request.method == 'GET':
        logger.info("🔍 GET запит до /webhook")
        return jsonify({
            "status": "webhook_ready",
            "bot": "@my_1qop1_bot",
            "methods": ["POST"],
            "description": "Telegram bot webhook endpoint",
            "railway_url": "https://sms-bot-production-4260.up.railway.app",
            "health_check": "/health"
        }), 200
    
    # Обробка POST запиту (повідомлення від Telegram)
    try:
        data = request.json
        if not data:
            return jsonify({"ok": True})
        
        logger.info(f"📨 Отримано від Telegram")
        
        # Оновлюємо час останньої активності
        bot_state["last_activity"] = time.time()
        
        # Обробка повідомлення
        if 'message' in data and 'text' in data['message']:
            text = data['message']['text'].strip()
            chat_id = data['message']['chat']['id']
            user_name = data['message']['chat'].get('first_name', 'користувач')
            
            logger.info(f"👤 {user_name}: {text}")
            
            # Обробка команд
            if text == '/start':
                response_text = f"""🤖 <b>Вітаю, {user_name}!</b>

Я бот для автоматичної реєстрації номерів телефонів.

<b>Команди:</b>
/register - Реєстрація номера
/sites - Список сайтів  
/status - Статус бота
/help - Допомога

<b>Сайти:</b>
• OLX.ua • Rozetka • Prom.ua • NovaPoshta • Epicentr"""
                
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": response_text,
                    "parse_mode": "HTML"
                })
            
            elif text == '/status':
                status_text = "✅ Готовий" if bot_state["ready"] else "⏳ Запускається"
                uptime = int(time.time() - bot_state["started_at"])
                
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"""<b>📊 Статус:</b>
• Бот: {status_text}
• Railway: ✅ Здоровий
• Час роботи: {uptime} сек
• Домен: sms-bot-production-4260.up.railway.app""",
                    "parse_mode": "HTML"
                })
            
            elif text == '/sites':
                sites_list = "\n".join([f"• {site}" for site in SITES_CONFIG.keys()])
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"""<b>🌐 Доступні сайти:</b>

{sites_list}

<b>Для реєстрації:</b>
1. Надішліть /register
2. Введіть номер +380XXXXXXXXX
3. Оберіть сайт""",
                    "parse_mode": "HTML"
                })
            
            elif text == '/register':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "📱 <b>Введіть номер телефону:</b>\n\nФормат: +380XXXXXXXXX\nПриклад: +380991234567",
                    "parse_mode": "HTML"
                })
            
            elif text == '/help':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": """<b>❓ Допомога:</b>

<b>Команди:</b>
/start - Початок
/register - Реєстрація
/sites - Сайти
/status - Статус

<b>Формат номера:</b>
+380XXXXXXXXX (13 символів)

<b>Підтримка:</b>
Звертайтеся з питаннями""",
                    "parse_mode": "HTML"
                })
            
            # Обробка номеру телефону
            elif text.startswith('+380') and len(text) == 13 and text[1:].isdigit():
                sites_buttons = []
                for site_name in list(SITES_CONFIG.keys())[:3]:  # Тільки перші 3 сайти
                    sites_buttons.append([{
                        "text": site_name,
                        "callback_data": f"register_{text}_{site_name.lower().replace('.', '')}"
                    }])
                
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"✅ <b>Отримано номер:</b> {text}\n\nОберіть сайт:",
                    "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": sites_buttons}
                })
            
            else:
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❓ Не розпізнана команда. Спробуйте /start або /help",
                    "parse_mode": "HTML"
                })
        
        # Обробка callback_query
        elif 'callback_query' in data:
            callback = data['callback_query']
            chat_id = callback['message']['chat']['id']
            callback_data = callback['data']
            
            if callback_data.startswith('register_'):
                parts = callback_data.split('_')
                if len(parts) >= 3:
                    phone = parts[1]
                    site = parts[2]
                    
                    # Відповідь користувачу
                    return jsonify({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": f"🔄 <b>Запускаю реєстрацію...</b>\n\n📱: {phone}\n🌐: {site}\n\n⏳ Зачекайте...",
                        "parse_mode": "HTML"
                    })
            
            # Відповідь на callback
            return jsonify({
                "method": "answerCallbackQuery",
                "callback_query_id": callback['id'],
                "text": "Оброблено!"
            })
    
    except Exception as e:
        logger.error(f"❌ Помилка обробки вебхука: {str(e)}")
    
    return jsonify({"ok": True})

# ========== HEALTHCHECK ==========

@app.route('/health')
def health():
    """Healthcheck для Railway"""
    if bot_state["ready"]:
        return jsonify({
            "status": "healthy",
            "selenium": "ready",
            "uptime": time.time() - bot_state["started_at"]
        }), 200
    elif bot_state["error"]:
        return jsonify({
            "status": "error",
            "error": bot_state["error"][:100]
        }), 500
    else:
        return jsonify({
            "status": "starting",
            "message": "Selenium ініціалізується..."
        }), 202

@app.route('/')
def home():
    """Головна сторінка"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Telegram Phone Bot</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: auto; padding: 20px; }
        .status { padding: 15px; border-radius: 5px; background: #e8f5e9; margin: 20px 0; }
        .btn { display: inline-block; background: #4CAF50; color: white; padding: 10px 20px; 
               text-decoration: none; border-radius: 5px; margin: 10px 5px; }
    </style>
</head>
<body>
    <h1>🤖 Telegram Phone Bot</h1>
    
    <div class="status">
        <h3>📊 Статус: {"✅ Працює" if bot_state["ready"] else "⏳ Запускається"}</h3>
        <p><b>🌐 Домен:</b> sms-bot-production-4260.up.railway.app</p>
        <p><b>🕒 Час роботи:</b> {int(time.time() - bot_state['started_at'])} сек</p>
    </div>
    
    <a href="https://t.me/my_1qop1_bot" class="btn" target="_blank">📱 Перейти до бота</a>
    <a href="/health" class="btn" target="_blank">🔍 Healthcheck</a>
    
    <h3>Команди бота:</h3>
    <ul>
        <li><code>/start</code> - Початок роботи</li>
        <li><code>/register</code> - Реєстрація номера</li>
        <li><code>/sites</code> - Список сайтів</li>
        <li><code>/status</code> - Статус системи</li>
        <li><code>/help</code> - Допомога</li>
    </ul>
</body>
</html>"""

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    # Запускаємо Selenium у фоні
    selenium_thread = threading.Thread(target=init_selenium, daemon=True)
    selenium_thread.start()
    logger.info("🔄 Запущено потік Selenium...")
    
    # Запускаємо Flask сервер
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Запуск сервера на порті {port}")
    logger.info(f"🤖 Бот: @my_1qop1_bot")
    
    app.run(host='0.0.0.0', port=port, debug=False)
