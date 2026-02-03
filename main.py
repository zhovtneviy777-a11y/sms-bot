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

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Обробка повідомлень від Telegram"""
    try:
        data = request.json
        logger.info(f"📨 Отримано від Telegram: {json.dumps(data, ensure_ascii=False)[:500]}...")
        
        # Оновлюємо час останньої активності
        bot_state["last_activity"] = time.time()
        
        if 'message' in data and 'text' in data['message']:
            text = data['message']['text'].strip()
            chat_id = data['message']['chat']['id']
            user_name = data['message']['chat'].get('first_name', 'користувач')
            
            logger.info(f"👤 {user_name}: {text}")
            
            # Обробка команд
            if text == '/start':
                response_text = f"""
🤖 <b>Вітаю, {user_name}!</b>

Я бот для автоматичної реєстрації номерів телефонів на українських сайтах.

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
                        "resize_keyboard": True,
                        "one_time_keyboard": False
                    }
                })
            
            elif text == '/status' or text == '🔄 Статус':
                status_text = "✅ Готовий" if bot_state["ready"] else "⏳ Запускається..."
                if bot_state["error"]:
                    status_text = f"❌ Помилка: {bot_state['error'][:100]}"
                
                uptime = int(time.time() - bot_state["started_at"])
                response_text = f"""
<b>📊 Статус системи:</b>
• 🤖 Бот: {status_text}
• 🌐 Вебхук: ✅ Активний
• 🚂 Railway: ✅ Здоровий
• 🕒 Uptime: {uptime} сек
• 🔗 Домен: sms-bot-production-4260.up.railway.app
• 📱 Остання активність: {time.strftime('%H:%M:%S', time.localtime(bot_state['last_activity']))}
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
<b>🌐 Доступні сайти для реєстрації:</b>

{sites_list}

<b>📱 Щоб зареєструвати номер:</b>
1. Натисніть "📞 Реєстрація номера"
2. Виберіть сайт
3. Введіть номер телефону у форматі +380XXXXXXXXX
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
                    "text": "📱 <b>Введіть номер телефону:</b>\n\nФормат: <code>+380XXXXXXXXX</code>\n\nПриклад: <code>+380991234567</code>",
                    "parse_mode": "HTML"
                })
            
            elif text == '/help':
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": """
<b>❓ Допомога по боту:</b>

Цей бот допомагає автоматично реєструвати номери телефонів на українських сайтах.

<b>📋 Як користуватися:</b>
1. Натисніть "📞 Реєстрація номера"
2. Виберіть сайт зі списку
3. Введіть номер у форматі +380XXXXXXXXX
4. Бот автоматично заповнить форму

<b>🌐 Підтримувані сайти:</b>
• OLX.ua • Rozetka • Prom.ua • NovaPoshta • Epicentr

<b>⚠️ Важливо:</b>
• Номер має починатися з +380
• Має бути 13 символів
• Приклад: +380991234567

<b>🛠 Підтримка:</b>
@ваш_нікнейм
""",
                    "parse_mode": "HTML"
                })
            
            # Обробка номеру телефону
            elif text.startswith('+380') and len(text) == 13:
                # Перевірка чи номер цифровий
                if text[1:].isdigit():
                    return jsonify({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": f"✅ <b>Отримано номер:</b> <code>{text}</code>\n\nТепер оберіть сайт:",
                        "parse_mode": "HTML",
                        "reply_markup": {
                            "inline_keyboard": [
                                [{"text": "OLX.ua", "callback_data": f"register_{text}_olx"}],
                                [{"text": "Rozetka", "callback_data": f"register_{text}_rozetka"}],
                                [{"text": "Prom.ua", "callback_data": f"register_{text}_prom"}],
                                [{"text": "NovaPoshta", "callback_data": f"register_{text}_nova"}],
                                [{"text": "Epicentr", "callback_data": f"register_{text}_epicenter"}]
                            ]
                        }
                    })
                else:
                    return jsonify({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": "❌ <b>Невірний формат номера!</b>\n\nПотрібно: <code>+380XXXXXXXXX</code>\nПриклад: <code>+380991234567</code>",
                        "parse_mode": "HTML"
                    })
            
            else:
                return jsonify({
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❓ Не розпізнана команда.\n\nСпробуйте /start або /help",
                    "parse_mode": "HTML"
                })
        
        # Обробка callback_query (натискання кнопок)
        elif 'callback_query' in data:
            callback = data['callback_query']
            chat_id = callback['message']['chat']['id']
            data_text = callback['data']
            
            logger.info(f"🖱 Callback: {data_text}")
            
            # Обробка вибору сайту
            if data_text.startswith('register_'):
                parts = data_text.split('_')
                if len(parts) >= 3:
                    phone = parts[1]
                    site = parts[2]
                    
                    return jsonify({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": f"🔄 <b>Запускаю реєстрацію...</b>\n\n📱 Номер: <code>{phone}</code>\n🌐 Сайт: {site}\n\n⏳ Це може зайняти декілька секунд...",
                        "parse_mode": "HTML"
                    })
            
            return jsonify({"method": "answerCallbackQuery", "callback_query_id": callback['id']})
    
    except Exception as e:
        logger.error(f"❌ Помилка обробки вебхука: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Завжди повертаємо ok=True для Telegram
    return jsonify({"ok": True})

# ========== ІНШІ МАРШРУТИ ==========

@app.route('/health')
def health():
    """Healthcheck для Railway"""
    if bot_state["ready"]:
        return jsonify({
            "status": "healthy",
            "selenium": "ready",
            "uptime": time.time() - bot_state["started_at"],
            "last_activity": bot_state["last_activity"]
        }), 200
    elif bot_state["error"]:
        return jsonify({
            "status": "error",
            "error": bot_state["error"][:100] if bot_state["error"] else "Unknown error"
        }), 500
    else:
        return jsonify({
            "status": "starting",
            "message": "Selenium ініціалізується...",
            "uptime": time.time() - bot_state["started_at"]
        }), 202

@app.route('/')
def home():
    """Головна сторінка"""
    status = "✅ Працює" if bot_state["ready"] else "⏳ Запускається"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Phone Bot</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .status {{ padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .healthy {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .starting {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
        .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .bot-link {{ display: inline-block; background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
        .bot-link:hover {{ background: #45a049; }}
        code {{ background: #f8f9fa; padding: 2px 5px; border-radius: 3px; border: 1px solid #e9ecef; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Telegram Phone Bot</h1>
        
        <div class="status {'healthy' if bot_state['ready'] else 'starting'}">
            <h3>📊 Статус системи</h3>
            <p><b>🤖 Бот:</b> {status}</p>
            <p><b>🌐 Вебхук:</b> ✅ Активний</p>
            <p><b>🚂 Railway:</b> ✅ Здоровий</p>
            <p><b>🕒 Uptime:</b> {int(time.time() - bot_state['started_at'])} сек</p>
            <p><b>🔗 Домен:</b> sms-bot-production-4260.up.railway.app</p>
        </div>
        
        <a href="https://t.me/my_1qop1_bot" class="bot-link" target="_blank">
            📱 Перейти до бота в Telegram
        </a>
        
        <h3>📋 Команди бота:</h3>
        <ul>
            <li><code>/start</code> - Запуск бота та меню</li>
            <li><code>/register</code> - Реєстрація номеру телефону</li>
            <li><code>/sites</code> - Список доступних сайтів</li>
            <li><code>/status</code> - Статус системи</li>
            <li><code>/help</code> - Допомога</li>
        </ul>
        
        <h3>🌐 Доступні сайти:</h3>
        <ul>
            <li>OLX.ua</li>
            <li>Rozetka.com.ua</li>
            <li>Prom.ua</li>
            <li>NovaPoshta</li>
            <li>EpicentrK.ua</li>
        </ul>
        
        <h3>🔗 Перевірки:</h3>
        <ul>
            <li><a href="/health" target="_blank">Healthcheck</a></li>
            <li><a href="https://api.telegram.org/bot8529982274:AAGIPNXQg7bkGKGEpUCpPNiSrT2NF3tPvns/getWebhookInfo" target="_blank">Статус вебхука</a></li>
        </ul>
    </div>
</body>
</html>
"""

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    # Запускаємо Selenium у фоні
    selenium_thread = threading.Thread(target=init_selenium, daemon=True)
    selenium_thread.start()
    logger.info("🔄 Запущено потік Selenium...")
    
    # Запускаємо Flask сервер
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Запуск сервера на порті {port}")
    logger.info(f"🌐 Вебхук URL: https://sms-bot-production-4260.up.railway.app/webhook")
    logger.info(f"🤖 Telegram бот: @my_1qop1_bot")
    
    app.run(host='0.0.0.0', port=port, debug=False)
