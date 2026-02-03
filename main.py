"""
Telegram Phone Bot - Головний файл
Автоматизація реєстрації телефонів на українських сайтах
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ініціалізація Flask
app = Flask(__name__)

# Завантажуємо змінні середовища
from dotenv import load_dotenv
load_dotenv()

# Конфігурація
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# Перевірка токена
if not BOT_TOKEN or BOT_TOKEN == "ваш_токен_бота_тут":
    logger.error("❌ ПОМИЛКА: BOT_TOKEN не налаштовано в .env файлі!")
    logger.error("Додайте BOT_TOKEN=ваш_реальний_токен у .env файл")
    exit(1)

# Конфігурація сайтів
SITES_CONFIG = {
    "OLX.ua": {
        "url": "https://www.olx.ua/uk/",
        "phone_selectors": [
            "input[type='tel']", 
            "input[name*='phone']",
            "input[name*='Phone']",
            "input[name*='PHONE']"
        ],
        "submit_selectors": [
            "button[type='submit']",
            "button[class*='submit']",
            "button[class*='btn-success']"
        ],
        "timeout": 15,
        "description": "Оголошення та продажі"
    },
    "Rozetka.com.ua": {
        "url": "https://rozetka.com.ua/",
        "phone_selectors": [
            "input[type='tel']", 
            "#auth_email",
            "input[name*='phone']",
            "input[name*='login']"
        ],
        "submit_selectors": [
            "button[type='submit']",
            "button[class*='submit']"
        ],
        "timeout": 15,
        "description": "Інтернет-магазин електроніки"
    },
    "Prom.ua": {
        "url": "https://prom.ua/",
        "phone_selectors": [
            "input[type='tel']", 
            "input[name*='phone']",
            "input[name*='Phone']"
        ],
        "submit_selectors": [
            "button[type='submit']",
            "button[class*='submit']"
        ],
        "timeout": 15,
        "description": "Маркетплейс"
    }
}

# Глобальний стан бота
bot_state = {
    "driver": None,
    "ready": False,
    "error": None,
    "started_at": time.time(),
    "last_activity": None,
    "total_requests": 0,
    "successful_operations": 0,
    "failed_operations": 0
}

def init_selenium():
    """Ініціалізація Selenium WebDriver для Docker/Heroku/Railway"""
    try:
        logger.info("🤖 Ініціалізація Selenium WebDriver...")
        
        # Налаштування середовища для Docker
        os.environ['CHROME_BIN'] = '/usr/bin/google-chrome'
        os.environ['CHROMEDRIVER_PATH'] = '/usr/local/bin/chromedriver'
        
        # Імпорт тут, щоб уникнути помилок якщо Selenium не встановлений
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        logger.info("Налаштування Chrome опцій...")
        
        # Опції для Chrome
        chrome_options = Options()
        
        # Обов'язкові опції для Docker
        chrome_options.add_argument("--headless=new")  # Новий headless режим
        chrome_options.add_argument("--no-sandbox")  # Необхідно для Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Для обмеженої пам'яті
        chrome_options.add_argument("--disable-gpu")  # Для віртуалізації
        
        # Оптимізація продуктивності
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-infobars")
        
        # Налаштування для обходу блокування
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Вказівка шляху до Chrome (для Railway)
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        # Додаткові заголовки
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        logger.info("Запуск Chrome WebDriver...")
        
        try:
            # Намагаємося запустити з вказаними опціями
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.warning(f"Перша спроба запуску невдала: {e}")
            logger.info("Спроба з іншими налаштуваннями...")
            
            # Спробуємо спрощені опції
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            driver = webdriver.Chrome(options=chrome_options)
        
        # Приховуємо автоматизацію
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Зберігаємо драйвер у стані
        bot_state["driver"] = driver
        bot_state["ready"] = True
        bot_state["last_activity"] = time.time()
        
        # Тестове відкриття сторінки
        logger.info("Виконуємо тестовий запит...")
        driver.get("https://www.google.com")
        logger.info(f"✅ Selenium готовий! Заголовок тестової сторінки: {driver.title}")
        
        bot_state["successful_operations"] += 1
        
    except Exception as e:
        error_msg = f"❌ Помилка ініціалізації Selenium: {str(e)}"
        logger.error(error_msg)
        bot_state["error"] = error_msg
        bot_state["failed_operations"] += 1

def send_telegram_message(chat_id, text, parse_mode="HTML"):
    """Надсилання повідомлення через Telegram Bot API"""
    import requests
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("ok"):
            logger.info(f"✅ Повідомлення надіслано до chat_id: {chat_id}")
            return True
        else:
            logger.error(f"❌ Помилка Telegram API: {response_data}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Помилка відправки повідомлення: {e}")
        return False

def process_phone_number(site_name, phone_number):
    """Обробка номеру телефону для конкретного сайту"""
    if not bot_state["ready"] or not bot_state["driver"]:
        return {"success": False, "error": "Selenium не готовий"}
    
    try:
        driver = bot_state["driver"]
        site_config = SITES_CONFIG.get(site_name)
        
        if not site_config:
            return {"success": False, "error": f"Сайт {site_name} не знайдено"}
        
        # Оновлюємо активність
        bot_state["last_activity"] = time.time()
        bot_state["total_requests"] += 1
        
        logger.info(f"🔧 Обробка для {site_name}, телефон: {phone_number}")
        
        # Відкриваємо сайт
        driver.get(site_config["url"])
        time.sleep(3)  # Чекаємо завантаження
        
        # Пошук поля для телефону
        phone_field = None
        for selector in site_config["phone_selectors"]:
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                element = WebDriverWait(driver, site_config["timeout"]).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element.is_displayed() and element.is_enabled():
                    phone_field = element
                    break
            except:
                continue
        
        if not phone_field:
            return {"success": False, "error": "Не знайдено поле для телефону"}
        
        # Вводимо номер телефону
        phone_field.clear()
        phone_field.send_keys(phone_number)
        
        # Пошук кнопки відправки
        submit_button = None
        for selector in site_config["submit_selectors"]:
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                element = WebDriverWait(driver, site_config["timeout"]).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                submit_button = element
                break
            except:
                continue
        
        if submit_button:
            submit_button.click()
            time.sleep(2)  # Чекаємо обробку
            
            bot_state["successful_operations"] += 1
            return {
                "success": True, 
                "message": f"Номер {phone_number} успішно введено на {site_name}",
                "site": site_name
            }
        else:
            bot_state["failed_operations"] += 1
            return {"success": False, "error": "Не знайдено кнопку відправки"}
            
    except Exception as e:
        error_msg = f"Помилка обробки: {str(e)}"
        logger.error(error_msg)
        bot_state["failed_operations"] += 1
        return {"success": False, "error": error_msg}

@app.route('/webhook', methods=['GET', 'POST'])
def telegram_webhook():
    """Обробник вебхуків від Telegram"""
    bot_state["last_activity"] = time.time()
    
    # GET запит - перевірка налаштування
    if request.method == 'GET':
        return jsonify({
            "status": "online",
            "bot": "Telegram Phone Bot",
            "webhook": "active",
            "selenium": "ready" if bot_state["ready"] else "starting",
            "uptime": int(time.time() - bot_state["started_at"])
        }), 200
    
    # POST запит - обробка повідомлень
    try:
        data = request.get_json()
        if not data:
            logger.info("Отримано пустий запит")
            return jsonify({"ok": True})
        
        logger.info(f"📨 Отримано дані від Telegram")
        
        # Обробка повідомлення
        if 'message' in data and 'text' in data['message']:
            message = data['message']
            text = message['text'].strip()
            chat_id = message['chat']['id']
            username = message['chat'].get('username', 'Невідомий')
            
            logger.info(f"👤 Користувач: @{username}, Текст: {text}")
            
            # Команда /start
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
            
            # Команда /status
            elif text == '/status':
                status_text = (
                    f"📊 *Статус бота*\n\n"
                    f"✅ Сервіс: {'Працює' if bot_state['ready'] else 'Запускається'}\n"
                    f"⏱ Аптайм: {int(time.time() - bot_state['started_at'])} сек\n"
                    f"📈 Запитів: {bot_state['total_requests']}\n"
                    f"✅ Успішно: {bot_state['successful_operations']}\n"
                    f"❌ Помилок: {bot_state['failed_operations']}\n"
                    f"🔄 Остання активність: {datetime.fromtimestamp(bot_state['last_activity']).strftime('%H:%M:%S')}\n\n"
                    f"🌐 Домен: sms-bot-production-4260.up.railway.app"
                )
                
                if bot_state['error']:
                    status_text += f"\n\n⚠️ *Помилка:* {bot_state['error']}"
                
                send_telegram_message(chat_id, status_text)
            
            # Команда /sites
            elif text == '/sites':
                sites_text = "🌐 *Доступні сайти:*\n\n"
                for site_name, config in SITES_CONFIG.items():
                    sites_text += f"• *{site_name}* - {config['description']}\n"
                
                sites_text += "\n📝 _Використання: /phone 380501234567 OLX.ua_"
                send_telegram_message(chat_id, sites_text)
            
            # Команда /phone
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
                    
                    # Валідація номеру
                    if not phone_number.isdigit() or len(phone_number) < 10:
                        send_telegram_message(
                            chat_id,
                            f"❌ *Неправильний номер телефону:* {phone_number}\n"
                            f"Приклад: 380501234567"
                        )
                    elif site_name not in SITES_CONFIG:
                        send_telegram_message(
                            chat_id,
                            f"❌ *Сайт не знайдено:* {site_name}\n"
                            f"Доступні сайти: /sites"
                        )
                    else:
                        # Відправляємо статус "в роботі"
                        send_telegram_message(
                            chat_id,
                            f"🔄 *Обробляємо запит...*\n"
                            f"📞 Номер: `{phone_number}`\n"
                            f"🌐 Сайт: {site_name}"
                        )
                        
                        # Обробляємо номер
                        result = process_phone_number(site_name, phone_number)
                        
                        if result["success"]:
                            send_telegram_message(
                                chat_id,
                                f"✅ *Успішно!*\n"
                                f"📞 Номер: `{phone_number}`\n"
                                f"🌐 Сайт: {site_name}\n"
                                f"📝 {result['message']}"
                            )
                        else:
                            send_telegram_message(
                                chat_id,
                                f"❌ *Помилка!*\n"
                                f"📞 Номер: `{phone_number}`\n"
                                f"🌐 Сайт: {site_name}\n"
                                f"⚠️ {result['error']}"
                            )
            
            # Команда /help
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
                    "*Підтримка:* @ваш_нікнейм"
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
        
        # Обробка callback-запитів (кнопки)
        elif 'callback_query' in data:
            callback_data = data['callback_query']['data']
            chat_id = data['callback_query']['message']['chat']['id']
            
            logger.info(f"🔘 Callback отримано: {callback_data}")
            send_telegram_message(chat_id, f"Отримано callback: {callback_data}")
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"❌ Помилка обробки вебхука: {e}")
        return jsonify({"ok": True})  # Все одно повертаємо ok для Telegram

@app.route('/health', methods=['GET'])
def health_check():
    """Ендпоінт для перевірки здоров'я (healthcheck)"""
    health_data = {
        "status": "healthy" if bot_state["ready"] else "starting",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(time.time() - bot_state["started_at"]),
        "selenium": "ready" if bot_state["ready"] else "not_ready",
        "total_requests": bot_state["total_requests"],
        "success_rate": f"{bot_state['successful_operations']}/{bot_state['total_requests']}" if bot_state['total_requests'] > 0 else "0/0",
        "last_activity": bot_state["last_activity"],
        "version": "1.0.0"
    }
    
    if bot_state["error"]:
        health_data["error"] = bot_state["error"]
        health_data["status"] = "error"
    
    status_code = 200 if bot_state["ready"] else 503 if bot_state["error"] else 202
    
    return jsonify(health_data), status_code

@app.route('/stats', methods=['GET'])
def get_stats():
    """Статистика роботи бота"""
    stats = {
        "bot": "Telegram Phone Bot",
        "start_time": datetime.fromtimestamp(bot_state["started_at"]).isoformat(),
        "uptime_hours": round((time.time() - bot_state["started_at"]) / 3600, 2),
        "requests": bot_state["total_requests"],
        "successful": bot_state["successful_operations"],
        "failed": bot_state["failed_operations"],
        "sites_configured": len(SITES_CONFIG),
        "memory_usage_mb": 0,  # Можна додати psutil для реальних даних
        "telegram_token_valid": bool(BOT_TOKEN)
    }
    
    return jsonify(stats), 200

@app.route('/', methods=['GET'])
def home():
    """Головна сторінка"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Telegram Phone Bot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                margin: 10px 0;
            }
            .ready { background: #4CAF50; }
            .starting { background: #FF9800; }
            .error { background: #F44336; }
            .links a {
                display: inline-block;
                margin: 10px;
                padding: 12px 24px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                transition: all 0.3s;
            }
            .links a:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
            .info-box {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            code {
                background: rgba(0, 0, 0, 0.3);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Phone Bot</h1>
            <p>Автоматизація введення номерів телефонів на українські сайти</p>
            
            <div class="info-box">
                <h2>📊 Статус системи</h2>
                <div class="status ''' + ('ready' if bot_state['ready'] else 'starting') + '''">
                    ''' + ('✅ Працює' if bot_state['ready'] else '⏳ Запускається') + '''
                </div>
                <p>Аптайм: ''' + str(int(time.time() - bot_state['started_at'])) + ''' секунд</p>
                <p>Запитів: ''' + str(bot_state['total_requests']) + '''</p>
            </div>
            
            <div class="info-box">
                <h2>🌐 Доступні сайти</h2>
                <ul>
                    <li>OLX.ua - оголошення та продажі</li>
                    <li>Rozetka.com.ua - інтернет-магазин</li>
                    <li>Prom.ua - маркетплейс</li>
                </ul>
            </div>
            
            <div class="links">
                <h2>🔗 Корисні посилання</h2>
                <a href="/health">🩺 Health Check</a>
                <a href="/stats">📈 Статистика</a>
                <a href="/webhook">🤖 Webhook Status</a>
            </div>
            
            <div class="info-box">
                <h2>📱 Використання в Telegram</h2>
                <p>Додайте бота: <code>@ваш_бот</code></p>
                <p>Команди: <code>/start</code>, <code>/status</code>, <code>/sites</code>, <code>/phone номер сайт</code></p>
                <p>Приклад: <code>/phone 380501234567 OLX.ua</code></p>
            </div>
            
            <footer style="margin-top: 40px; text-align: center; opacity: 0.8;">
                <p>© 2024 Telegram Phone Bot | Працює на Railway</p>
            </footer>
        </div>
    </body>
    </html>
    '''

@app.route('/test', methods=['GET'])
def test_page():
    """Тестова сторінка"""
    return '''
    <h1>Тестова сторінка</h1>
    <p>Якщо ви бачите цей текст, Flask працює!</p>
    <p><a href="/">На головну</a></p>
    '''

# Ініціалізація Selenium у фоновому потоці
if not os.environ.get('SKIP_SELENIUM'):
    selenium_thread = threading.Thread(target=init_selenium, daemon=True)
    selenium_thread.start()
    logger.info("🚀 Запущено фонову ініціалізацію Selenium")
else:
    logger.info("⏭️ Пропущено ініціалізацію Selenium (SKIP_SELENIUM=true)")

# Важливо: НЕ використовуємо if __name__ == '__main__' для Railway!
# Railway запускає через gunicorn

# Для локального запуску (не для Railway)
if __name__ == '__main__':
    logger.info(f"🚀 Запуск локального сервера на порті {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
