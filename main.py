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
    "started_at": time.time(),
    "telegram_webhook": "https://sms-bot-production-4260.up.railway.app/webhook"
}

def init_selenium():
    """Ініціалізація Selenium"""
    global bot_status
    
    try:
        logger.info("🤖 Запускаємо Selenium для реєстрації номерів...")
        time.sleep(10)
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        bot_status["driver"] = driver
        bot_status["ready"] = True
        
        logger.info("✅ Selenium готовий до роботи з номерами!")
        
    except Exception as e:
        bot_status["error"] = str(e)
        logger.error(f"❌ Помилка Selenium: {e}")

# ========== TELEGRAM WEBHOOK HANDLERS ==========

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Обробка повідомлень від Telegram"""
    try:
        data = request.json
        logger.info(f"📨 Отримано від Telegram: {data}")
        
        if 'message' in data and 'text' in data['message']:
            text = data['message']['text']
            chat_id = data['message']['chat']['id']
            first_name = data['message']['chat'].get('first_name', 'користувач')
            
            logger.info(f"👤 {first_name}: {text}")
            
            # Обробка команд
            if text == '/start':
                response_text = f"""
🤖 <b>Вітаю, {first_name}!</b>

Це бот для автоматичної реєстрації номерів телефонів на українських сайтах.

<b>Доступні команди:</b>
/register - Реєстрація номеру телефону
/sites - Список доступних сайтів
/status - Статус бота
/help - Допомога

<b>Доступні сайти:</b>
• OLX.ua
• Rozetka.com.ua  
• Prom.ua
• NovaPoshta
• EpicentrK.ua

🌐 <b>Домен:</b> sms-bot-production-4260.up.railway.app
"""
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": response_text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "keyboard": [
                            [{"text": "📋 Список сайтів"}],
                            [{"text": "📞 Реєстрація номера"}],
                            [{"text": "🔄 Статус"}]
                        ],
                        "resize_keyboard": True
                    }
                })
            
            elif text == '/status' or text == '🔄 Статус':
                status_text = "✅ Готовий" if bot_status["ready"] else "⏳ Запускається..."
                response_text = f"""
<b>Статус системи:</b>
• 🤖 Бот: {status_text}
• 🌐 Вебхук: Активний
• 🚂 Railway: Здоровий
• 🕒 Uptime: {int(time.time() - bot_status['started_at'])} сек
• 🔗 Домен: sms-bot-production-4260.up.railway.app
"""
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": response_text,
                    "parse_mode": "HTML"
                })
            
            elif text == '/sites' or text == '📋 Список сайтів':
                sites_list = "\n".join([f"• {site}" for site in SITES_CONFIG.keys()])
                response_text = f"""
<b>Доступні сайти для реєстрації:</b>

{sites_list}

<b>Щоб зареєструвати номер:</b>
1. Натисніть "📞 Реєстрація номера"
2. Виберіть сайт
3. Введіть номер телефону
"""
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": response_text,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "OLX.ua", "callback_data": "site_olx"}],
                            [{"text": "Rozetka", "callback_data": "site_rozetka"}],
                            [{"text": "Prom.ua", "callback_data": "site_prom"}],
                            [{"text": "NovaPoshta", "callback_data": "site_nova"}],
                            [{"text": "Epicentr", "callback_data": "site_epicenter"}]
                        ]
                    }
                })
            
            elif text == '/register' or text == '📞 Реєстрація номера':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "📱 <b>Введіть номер телефону:</b>\n\nФормат: +380XXXXXXXXX",
                    "parse_mode": "HTML"
                })
            
            elif text == '/help':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": """
<b>Допомога по боту:</b>

Цей бот допомагає автоматично реєструвати номери телефонів на українських сайтах.

<b>Як користуватися:</b>
1. Натисніть "📞 Реєстрація номера"
2. Виберіть сайт зі списку
3. Введіть номер у форматі +380XXXXXXXXX
4. Бот автоматично заповнить форму

<b>Підтримувані сайти:</b>
• OLX.ua • Rozetka • Prom.ua • NovaPoshta • Epicentr

<b>Підтримка:</b>
@ваш_нікнейм
""",
                    "parse_mode": "HTML"
                })
            
            # Обробка номеру телефону
            elif text.startswith('+380') and len(text) == 13:
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"📱 <b>Отримано номер:</b> {text}\n\nТепер оберіть сайт:",
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "OLX.ua", "callback_data": f"register_{text}_olx"}],
                            [{"text": "Rozetka", "callback_data": f"register_{text}_rozetka"}],
                            [{"text": "Prom.ua", "callback_data": f"register_{text}_prom"}]
                        ]
                    }
                })
            
            else:
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "Не розпізнана команда. Спробуйте /start",
                    "parse_mode": "HTML"
                })
    
    except Exception as e:
        logger.error(f"❌ Помилка обробки вебхука: {e}")
    
    return jsonify({"ok": True})

@app.route('/health')
def health():
    """Healthcheck для Railway"""
    if bot_status["ready"]:
        return jsonify({
            "status": "healthy",
            "selenium": "ready",
            "uptime": time.time() - bot_status["started_at"]
        }), 200
    elif bot_status["error"]:
        return jsonify({
            "status": "error",
            "error": bot_status["error"]
        }), 500
    else:
        return jsonify({
            "status": "starting",
            "message": "Selenium ініціалізується..."
        }), 202

@app.route('/')
def home():
    """Головна сторінка з інформацією про бота"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Phone Bot</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .healthy { background: #d4edda; color: #155724; }
        .starting { background: #fff3cd; color: #856404; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>🤖 Telegram Phone Bot</h1>
    
    <p>Бот працює успішно!</p>
    <p>Домен: <b>sms-bot-production-4260.up.railway.app</b></p>
    
    <div class="status """ + ("healthy" if bot_status["ready"] else "starting") + """">
        <h3>Статус системи:</h3>
        <p>🤖 Бот: """ + ("✅ Працює" if bot_status["ready"] else "⏳ Налаштовується") + """</p>
        <p>🌐 Вебхук: ✅ Активний</p>
        <p>🚂 Railway: ✅ Здоровий</p>
        <p>🕒 Uptime: """ + str(int(time.time() - bot_status["started_at"])) + """ сек</p>
    </div>
    
    <h3>Команди:</h3>
    <ul>
        <li><code>/start</code> - Запуск бота</li>
        <li><code>/register</code> - Реєстрація номеру</li>
        <li><code>/sites</code> - Список сайтів</li>
        <li><code>/status</code> - Статус системи</li>
        <li><code>/help</code> - Допомога</li>
    </ul>
    
    <h3>Доступні сайти:</h3>
    <ul>
        <li>OLX.ua</li>
        <li>Rozetka.com.ua</li>
        <li>Prom.ua</li>
        <li>NovaPoshta</li>
        <li>EpicentrK.ua</li>
    </ul>
</body>
</html>
"""

# Запускаємо Selenium у фоні
threading.Thread(target=init_selenium, daemon=True).start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Запуск бота на порту {port}")
    logger.info(f"🌐 Вебхук: {bot_status['telegram_webhook']}")
    app.run(host='0.0.0.0', port=port, debug=False)
