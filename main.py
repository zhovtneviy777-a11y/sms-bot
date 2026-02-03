"""
Telegram Phone Bot - Flask версія
Без aiogram, тільки Flask + вебхуки
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# ================= НАЛАШТУВАННЯ =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Завантажуємо змінні середовища
from dotenv import load_dotenv
load_dotenv()

# Отримуємо токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not BOT_TOKEN or BOT_TOKEN == "ваш_токен_бота_тут":
    logger.warning("⚠️ BOT_TOKEN не налаштовано або залишився шаблонний")
    logger.warning("Бот працюватиме, але не зможе відправляти повідомлення")
    BOT_TOKEN = None

# ================= СТАН БОТА =================
bot_state = {
    "ready": True,
    "started_at": time.time(),
    "last_activity": time.time(),
    "total_requests": 0,
    "webhook_set": True,
    "bot_username": "@my_1qop1_bot"
}

# ================= ДОПОМІЖНІ ФУНКЦІЇ =================
def send_telegram_message(chat_id, text, parse_mode="HTML"):
    """Надсилає повідомлення через Telegram Bot API"""
    if not BOT_TOKEN:
        logger.warning(f"Не можу відправити повідомлення: BOT_TOKEN не налаштовано")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get("ok"):
            logger.info(f"✅ Повідомлення надіслано до {chat_id}")
            return True
        else:
            logger.error(f"❌ Помилка Telegram API: {data}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Таймаут при відправці повідомлення")
        return False
    except Exception as e:
        logger.error(f"❌ Помилка відправки: {e}")
        return False

def get_bot_info():
    """Отримує інформацію про бота"""
    if not BOT_TOKEN:
        return {"error": "Токен не налаштовано"}
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ================= WEBHOOK ENDPOINT =================
@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    """Обробник вебхуків від Telegram"""
    bot_state["last_activity"] = time.time()
    bot_state["total_requests"] += 1
    
    # GET запит - перевірка налаштування
    if request.method == 'GET':
        return jsonify({
            "status": "active",
            "service": "Telegram Webhook",
            "bot": bot_state["bot_username"],
            "webhook_url": "https://sms-bot-production-4260.up.railway.app/webhook",
            "uptime": int(time.time() - bot_state["started_at"]),
            "total_requests": bot_state["total_requests"]
        }), 200
    
    # POST запит - обробка повідомлень
    try:
        data = request.get_json()
        if not data:
            logger.info("📭 Отримано пустий запит")
            return jsonify({"ok": True})
        
        logger.info(f"📨 Отримано запит від Telegram")
        
        # Обробка повідомлення
        if 'message' in data and 'text' in data['message']:
            message = data['message']
            text = message['text'].strip()
            chat_id = message['chat']['id']
            
            # Логуємо
            logger.info(f"👤 Chat ID: {chat_id}, Команда: {text}")
            
            # --- ОБРОБКА КОМАНД ---
            
            # /start
            if text == '/start':
                welcome_text = (
                    "🤖 *Вітаю! Я Phone Registration Bot*\n\n"
                    "Я допомагаю автоматизувати введення номерів телефонів "
                    "на українські сайти.\n\n"
                    "*Доступні команди:*\n"
                    "📊 /status - статус бота\n"
                    "🌐 /sites - список сайтів\n"
                    "📞 /phone <номер> <сайт> - відправити номер\n"
                    "❓ /help - допомога\n\n"
                    "_Приклад: /phone 380501234567 OLX.ua_"
                )
                send_telegram_message(chat_id, welcome_text)
            
            # /status
            elif text == '/status':
                # Отримуємо інфо про бота
                bot_info = get_bot_info()
                bot_name = "невідомий"
                
                if "result" in bot_info:
                    bot_name = f"@{bot_info['result']['username']}"
                
                status_text = (
                    f"📊 *Статус бота*\n\n"
                    f"✅ Сервіс: Працює\n"
                    f"🤖 Бот: {bot_name}\n"
                    f"⏱ Аптайм: {int(time.time() - bot_state['started_at'])} сек\n"
                    f"📈 Запитів: {bot_state['total_requests']}\n"
                    f"🔄 Остання активність: {datetime.fromtimestamp(bot_state['last_activity']).strftime('%H:%M:%S')}\n\n"
                    f"🌐 Домен: sms-bot-production-4260.up.railway.app\n"
                    f"🔗 Вебхук: Налаштовано"
                )
                
                send_telegram_message(chat_id, status_text)
            
            # /sites
            elif text == '/sites':
                sites_text = (
                    "🌐 *Доступні сайти:*\n\n"
                    "• *OLX.ua* - оголошення та продажі\n"
                    "• *Rozetka.com.ua* - інтернет-магазин електроніки\n"
                    "• *Prom.ua* - маркетплейс\n"
                    "• *NovaPoshta* - служба доставки\n"
                    "• *EpicentrK.ua* - будівельний гіпермаркет\n\n"
                    "📝 *Використання:*\n"
                    "`/phone 380501234567 OLX.ua`"
                )
                send_telegram_message(chat_id, sites_text)
            
            # /phone
            elif text.startswith('/phone'):
                parts = text.split()
                if len(parts) < 3:
                    send_telegram_message(
                        chat_id, 
                        "❌ *Неправильний формат!*\n\n"
                        "Приклад: `/phone 380501234567 OLX.ua`\n"
                        "Список сайтів: /sites"
                    )
                else:
                    phone_number = parts[1]
                    site_name = ' '.join(parts[2:])
                    
                    # Симулюємо обробку
                    send_telegram_message(
                        chat_id,
                        f"🔄 *Обробка запиту...*\n"
                        f"📞 Номер: `{phone_number}`\n"
                        f"🌐 Сайт: {site_name}\n"
                        f"⏳ Зачекайте кілька секунд..."
                    )
                    
                    # Чекаємо (імітація обробки)
                    time.sleep(2)
                    
                    # Результат
                    send_telegram_message(
                        chat_id,
                        f"✅ *Запит оброблено!*\n"
                        f"📞 Номер: `{phone_number}`\n"
                        f"🌐 Сайт: {site_name}\n"
                        f"📊 Статус: Введено успішно\n\n"
                        f"_Це демонстраційний режим_"
                    )
            
            # /help
            elif text == '/help':
                help_text = (
                    "❓ *Довідка по командам:*\n\n"
                    "📊 /status - перевірити статус бота\n"
                    "🌐 /sites - список доступних сайтів\n"
                    "📞 /phone <номер> <сайт> - відправити номер телефону\n"
                    "❓ /help - ця довідка\n\n"
                    "*Приклади використання:*\n"
                    "`/phone 380501234567 OLX.ua`\n"
                    "`/phone 380671234567 Rozetka.com.ua`\n\n"
                    "*Примітка:* Зараз бот працює в демо-режимі"
                )
                send_telegram_message(chat_id, help_text)
            
            # Невідома команда
            else:
                send_telegram_message(
                    chat_id,
                    "❓ *Невідома команда*\n\n"
                    "Доступні команди:\n"
                    "/start - початок роботи\n"
                    "/status - статус бота\n"
                    "/sites - список сайтів\n"
                    "/phone - відправити номер\n"
                    "/help - допомога"
                )
        
        # Обробка callback_query (кнопки)
        elif 'callback_query' in data:
            callback = data['callback_query']
            chat_id = callback['message']['chat']['id']
            callback_data = callback.get('data', '')
            
            logger.info(f"🔘 Callback отримано: {callback_data}")
            send_telegram_message(chat_id, f"Отримано callback: {callback_data}")
        
        # Відповідь на inline запити
        elif 'inline_query' in data:
            logger.info(f"🔍 Inline query отримано")
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"❌ Помилка обробки вебхука: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": True, "error": str(e)})

# ================= ДОПОМІЖНІ ENDPOINTS =================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check для Railway"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Telegram Phone Bot",
        "bot": bot_state["bot_username"],
        "uptime_seconds": int(time.time() - bot_state["started_at"]),
        "total_requests": bot_state["total_requests"],
        "last_activity": bot_state["last_activity"],
        "webhook_active": bot_state["webhook_set"],
        "version": "1.0.0"
    }
    
    # Перевірка токена
    if not BOT_TOKEN:
        health_status["bot_token"] = "not_configured"
        health_status["warning"] = "BOT_TOKEN не налаштовано"
    else:
        health_status["bot_token"] = "configured"
    
    return jsonify(health_status), 200

@app.route('/info', methods=['GET'])
def bot_info():
    """Інформація про бота"""
    info = {
        "project": "Telegram Phone Bot",
        "description": "Бот для автоматизації введення номерів телефонів",
        "author": "Your Name",
        "version": "1.0.0",
        "endpoints": {
            "/": "Головна сторінка",
            "/webhook": "Telegram вебхук (GET/POST)",
            "/health": "Перевірка здоров'я",
            "/info": "Ця сторінка",
            "/stats": "Статистика",
            "/test": "Тестовий endpoint"
        },
        "telegram_bot": bot_state["bot_username"],
        "webhook_url": "https://sms-bot-production-4260.up.railway.app/webhook"
    }
    
    return jsonify(info), 200

@app.route('/stats', methods=['GET'])
def statistics():
    """Статистика роботи"""
    stats = {
        "bot": bot_state["bot_username"],
        "start_time": datetime.fromtimestamp(bot_state["started_at"]).isoformat(),
        "uptime_hours": round((time.time() - bot_state["started_at"]) / 3600, 2),
        "total_requests": bot_state["total_requests"],
        "last_activity": datetime.fromtimestamp(bot_state["last_activity"]).isoformat(),
        "current_time": datetime.now().isoformat(),
        "telegram_webhook": "active"
    }
    
    return jsonify(stats), 200

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Тестовий endpoint"""
    return jsonify({
        "message": "Бот працює!",
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }), 200

# ================= ГОЛОВНА СТОРІНКА =================
@app.route('/', methods=['GET'])
def home():
    """Головна сторінка"""
    return '''
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 Telegram Phone Bot</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
            
            h1 {
                font-size: 2.8em;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .tagline {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 40px;
            }
            
            .status-badge {
                display: inline-block;
                padding: 8px 20px;
                background: #4CAF50;
                border-radius: 50px;
                font-weight: bold;
                margin: 20px 0;
                font-size: 1.1em;
            }
            
            .card {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 15px;
                padding: 25px;
                margin: 25px 0;
                transition: transform 0.3s;
            }
            
            .card:hover {
                transform: translateY(-5px);
            }
            
            .card h3 {
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .endpoints {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .endpoint {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #4CAF50;
            }
            
            .endpoint .method {
                display: inline-block;
                padding: 4px 12px;
                background: #4CAF50;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
                font-size: 0.9em;
            }
            
            .buttons {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin: 40px 0;
            }
            
            .btn {
                padding: 12px 30px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                transition: all 0.3s;
                border: 2px solid rgba(255, 255, 255, 0.3);
                font-weight: bold;
                display: inline-flex;
                align-items: center;
                gap: 10px;
            }
            
            .btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
                border-color: white;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .stat-item {
                text-align: center;
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #4CAF50;
            }
            
            .stat-label {
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            footer {
                margin-top: 50px;
                text-align: center;
                opacity: 0.7;
                font-size: 0.9em;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                
                h1 {
                    font-size: 2em;
                }
                
                .endpoints {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Phone Bot</h1>
            <p class="tagline">Автоматизація введення номерів телефонів на українські сайти</p>
            
            <div class="status-badge">✅ Сервіс активний</div>
            
            <div class="card">
                <h3>📱 Про бота</h3>
                <p>Цей бот допомагає автоматизувати процес введення номерів телефонів на популярних українських сайтах. Він працює через Telegram вебхуки та готовий до використання.</p>
            </div>
            
            <div class="buttons">
                <a href="https://t.me/my_1qop1_bot" class="btn" target="_blank">
                    <span>🤖</span> Відкрити в Telegram
                </a>
                <a href="/health" class="btn">
                    <span>🩺</span> Health Check
                </a>
                <a href="/info" class="btn">
                    <span>ℹ️</span> Інформація
                </a>
                <a href="/stats" class="btn">
                    <span>📈</span> Статистика
                </a>
            </div>
            
            <div class="card">
                <h3>🌐 Доступні сайти</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">• OLX.ua</div>
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">• Rozetka.com.ua</div>
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">• Prom.ua</div>
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">• NovaPoshta</div>
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">• EpicentrK.ua</div>
                </div>
            </div>
            
            <div class="card">
                <h3>🔗 API Endpoints</h3>
                <div class="endpoints">
                    <div class="endpoint">
                        <div><span class="method">GET/POST</span> <strong>/webhook</strong></div>
                        <div style="margin-top: 8px; font-size: 0.9em; opacity: 0.8;">Telegram вебхук для обробки повідомлень</div>
                    </div>
                    <div class="endpoint">
                        <div><span class="method">GET</span> <strong>/health</strong></div>
                        <div style="margin-top: 8px; font-size: 0.9em; opacity: 0.8;">Перевірка стану сервісу (для Railway)</div>
                    </div>
                    <div class="endpoint">
                        <div><span class="method">GET</span> <strong>/stats</strong></div>
                        <div style="margin-top: 8px; font-size: 0.9em; opacity: 0.8;">Статистика роботи бота</div>
                    </div>
                    <div class="endpoint">
                        <div><span class="method">GET</span> <strong>/info</strong></div>
                        <div style="margin-top: 8px; font-size: 0.9em; opacity: 0.8;">Інформація про проєкт</div>
                    </div>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="uptime">0</div>
                    <div class="stat-label">секунд аптайму</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="requests">''' + str(bot_state["total_requests"]) + '''</div>
                    <div class="stat-label">запитів</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">24/7</div>
                    <div class="stat-label">доступність</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">5</div>
                    <div class="stat-label">сайтів</div>
                </div>
            </div>
            
            <footer>
                <p>© 2024 Telegram Phone Bot | Працює на <a href="https://railway.app" style="color: white; text-decoration: underline;">Railway</a></p>
                <p style="margin-top: 10px; font-size: 0.8em;">Версія 1.0.0 | Flask без aiogram</p>
            </footer>
        </div>
        
        <script>
            // Оновлення аптайму
            function updateUptime() {
                const startTime = ''' + str(bot_state["started_at"]) + ''';
                const now = Math.floor(Date.now() / 1000);
                const uptime = now - startTime;
                document.getElementById('uptime').textContent = uptime.toLocaleString();
            }
            
            updateUptime();
            setInterval(updateUptime, 1000);
        </script>
    </body>
    </html>
    '''

# ================= ЗАПУСК =================
# Важливо: НЕ використовуємо if __name__ == '__main__' для Railway!
# Railway запускає через gunicorn

# Якщо потрібно для локального запуску
if __name__ == '__main__':
    logger.info(f"🚀 Запуск сервера на порті {PORT}")
    logger.info(f"🌐 Вебхук URL: https://sms-bot-production-4260.up.railway.app/webhook")
    logger.info(f"🤖 Бот: {bot_state['bot_username']}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
