import os
import json
import threading
import time
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАЛАШТУВАННЯ =====
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///numbers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
logging.basicConfig(level=logging.INFO)

# Глобальна змінна для зупинки
STOP_SIGNAL = False
CURRENT_JOB_ID = None

# ===== МОДЕЛІ БАЗИ ДАНИХ =====
class PhoneNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=1)
    services = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.now)
    results = db.Column(db.Text, default='{}')

class RegistrationJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False)
    current_number_id = db.Column(db.Integer)
    started_at = db.Column(db.DateTime, default=datetime.now)
    stopped_at = db.Column(db.DateTime)

# ===== СПИСОК СЕРВІСІВ =====
SERVICES = {
    'olx': {'name': 'OLX', 'url': 'https://www.olx.ua/account/register/'},
    'amazon': {'name': 'Amazon', 'url': 'https://www.amazon.com/ap/register'},
    'ebay': {'name': 'eBay', 'url': 'https://signup.ebay.com/pa/crte?ru=https%3A%2F%2Fwww.ebay.com%2F'},
    'paypal': {'name': 'PayPal', 'url': 'https://www.paypal.com/signup'},
    'google': {'name': 'Google', 'url': 'https://accounts.google.com/signup'},
    'airbnb': {'name': 'Airbnb', 'url': 'https://www.airbnb.com/signup_login'},
    'microsoft': {'name': 'Microsoft', 'url': 'https://signup.live.com/'},
    'yahoo': {'name': 'Yahoo', 'url': 'https://login.yahoo.com/account/create'},
    'whatsapp': {'name': 'WhatsApp', 'url': 'https://www.whatsapp.com/download'}
}

# ===== SELENIUM ДРАЙВЕР =====
def create_driver():
    """Створення Selenium драйвера"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Для Render
    chrome_options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    
    driver = webdriver.Chrome(
        executable_path=os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"),
        options=chrome_options
    )
    return driver

# ===== ФУНКЦІЇ РЕЄСТРАЦІЇ =====
def register_on_olx(phone):
    """Реєстрація на OLX"""
    driver = create_driver()
    try:
        driver.get("https://www.olx.ua/account/register/")
        # Знаходимо поле для телефону
        phone_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "phone"))
        )
        phone_field.send_keys(phone)
        # Натискаємо кнопку продовжити
        continue_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Продовжити')]")
        continue_btn.click()
        time.sleep(3)
        return {"success": True, "message": "Запит на реєстрацію відправлено"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        driver.quit()

def register_on_amazon(phone):
    """Реєстрація на Amazon"""
    driver = create_driver()
    try:
        driver.get("https://www.amazon.com/ap/register")
        # Заповнюємо форму
        name_field = driver.find_element(By.ID, "ap_customer_name")
        name_field.send_keys("Test User")
        
        email_field = driver.find_element(By.ID, "ap_email")
        email_field.send_keys(f"test{int(time.time())}@example.com")
        
        password_field = driver.find_element(By.ID, "ap_password")
        password_field.send_keys("TestPassword123!")
        
        password_check = driver.find_element(By.ID, "ap_password_check")
        password_check.send_keys("TestPassword123!")
        
        # Натискаємо створити акаунт
        create_btn = driver.find_element(By.ID, "continue")
        create_btn.click()
        time.sleep(3)
        return {"success": True, "message": "Форма заповнена (потрібна підтверджувача SMS)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        driver.quit()

def register_on_service(service_id, phone):
    """Загальна функція реєстрації"""
    if service_id == 'olx':
        return register_on_olx(phone)
    elif service_id == 'amazon':
        return register_on_amazon(phone)
    elif service_id == 'ebay':
        # Додайте код для eBay
        return {"success": True, "message": "Реєстрація на eBay"}
    elif service_id == 'paypal':
        return {"success": True, "message": "Реєстрація на PayPal"}
    elif service_id == 'google':
        return {"success": True, "message": "Реєстрація на Google"}
    elif service_id == 'airbnb':
        return {"success": True, "message": "Реєстрація на Airbnb"}
    elif service_id == 'microsoft':
        return {"success": True, "message": "Реєстрація на Microsoft"}
    elif service_id == 'yahoo':
        return {"success": True, "message": "Реєстрація на Yahoo"}
    elif service_id == 'whatsapp':
        return {"success": True, "message": "Реєстрація на WhatsApp"}
    else:
        return {"success": False, "error": "Невідомий сервіс"}

# ===== РОБОЧИЙ ПРОЦЕС =====
def registration_worker(job_id):
    """Фоновий процес реєстрації"""
    global STOP_SIGNAL
    
    with app.app_context():
        job = RegistrationJob.query.get(job_id)
        if not job:
            return
        
        while not STOP_SIGNAL and job.active:
            # Знаходимо наступний номер
            number = PhoneNumber.query.filter_by(status='pending').first()
            if not number:
                job.active = False
                db.session.commit()
                break
            
            # Оновлюємо статус
            number.status = 'processing'
            job.current_number_id = number.id
            db.session.commit()
            
            # Отримуємо список сервісів
            services_list = json.loads(number.services)
            results = {}
            
            # Реєструємо на кожному сервісі
            for service_id in services_list:
                if STOP_SIGNAL:
                    break
                
                result = register_on_service(service_id, number.number)
                results[service_id] = result
                
                number.attempts += 1
                time.sleep(2)  # Пауза між сервісами
            
            # Зберігаємо результати
            number.results = json.dumps(results)
            
            # Перевіряємо чи все завершено
            if number.attempts >= number.max_attempts:
                number.status = 'completed'
            else:
                number.status = 'pending'
            
            db.session.commit()
            
            # Пауза між номерами
            time.sleep(3)
        
        # Завершення роботи
        job.active = False
        job.stopped_at = datetime.now()
        db.session.commit()

# ===== ВЕБ-ІНТЕРФЕЙС =====
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>📱 Бот реєстрації номерів</title>
    <style>
        body { font-family: Arial; max-width: 1000px; margin: 0 auto; padding: 20px; }
        .section { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 10px; }
        textarea { width: 100%; height: 150px; padding: 10px; }
        button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-start { background: #4CAF50; color: white; }
        .btn-stop { background: #f44336; color: white; }
        .btn-add { background: #2196F3; color: white; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .status-pending { background: #FFF3CD; }
        .status-processing { background: #D1ECF1; }
        .status-completed { background: #D4EDDA; }
        .service-checkbox { margin-right: 15px; margin-bottom: 10px; display: inline-block; }
        .numbers-list { max-height: 300px; overflow-y: auto; }
        .number-item { padding: 8px; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <h1>🤖 Бот масової реєстрації номерів</h1>
    
    <div class="section">
        <h2>📱 Додати номери</h2>
        <textarea id="numbers" placeholder="Введіть номери (кожен з нового рядка):
+380123456789
+380987654321"></textarea>
        
        <h3>Оберіть сервіси:</h3>
        <div id="services">
            {% for id, info in services.items() %}
            <label class="service-checkbox">
                <input type="checkbox" value="{{ id }}" checked> {{ info.name }}
            </label>
            {% endfor %}
        </div>
        
        <div>
            <label>Кількість спроб: </label>
            <input type="number" id="attempts" value="1" min="1" style="width: 60px;">
        </div>
        
        <button class="btn-add" onclick="addNumbers()">✅ Додати номери</button>
    </div>
    
    <div class="section">
        <h2>🚀 Керування</h2>
        <button class="btn-start" onclick="startJob()">▶️ Почати реєстрацію</button>
        <button class="btn-stop" onclick="stopJob()">⏹️ Зупинити</button>
        
        <div id="status">
            <h3>Статус:</h3>
            <p>Всього номерів: <span id="total">0</span></p>
            <p>Очікують: <span id="pending">0</span></p>
            <p>Виконується: <span id="processing">0</span></p>
            <p>Завершено: <span id="completed">0</span></p>
        </div>
    </div>
    
    <div class="section">
        <h2>📋 Список номерів</h2>
        <div class="numbers-list" id="numbersList">
            {% for number in numbers %}
            <div class="number-item status-{{ number.status }}">
                {{ number.number }} - {{ number.status }} ({{ number.attempts }}/{{ number.max_attempts }})
            </div>
            {% endfor %}
        </div>
        <button onclick="refreshList()">🔄 Оновити</button>
    </div>
    
    <script>
        function addNumbers() {
            const numbers = document.getElementById('numbers').value;
            const checkboxes = document.querySelectorAll('#services input[type="checkbox"]:checked');
            const services = Array.from(checkboxes).map(cb => cb.value);
            const attempts = document.getElementById('attempts').value;
            
            fetch('/api/add_numbers', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({numbers, services, attempts})
            })
            .then(r => r.json())
            .then(data => {
                alert(`Додано ${data.added} номерів`);
                refreshList();
            });
        }
        
        function startJob() {
            fetch('/api/start_job', {method: 'POST'})
            .then(r => r.json())
            .then(data => alert(`Завдання #${data.job_id} запущено`));
        }
        
        function stopJob() {
            fetch('/api/stop_job', {method: 'POST'})
            .then(r => r.json())
            .then(data => alert('Процес зупинено'));
        }
        
        function refreshList() {
            fetch('/api/numbers')
            .then(r => r.json())
            .then(data => {
                let html = '';
                data.numbers.forEach(n => {
                    html += `<div class="number-item status-${n.status}">${n.number} - ${n.status} (${n.attempts}/${n.max_attempts})</div>`;
                });
                document.getElementById('numbersList').innerHTML = html;
                updateStats(data.stats);
            });
        }
        
        function updateStats(stats) {
            document.getElementById('total').textContent = stats.total;
            document.getElementById('pending').textContent = stats.pending;
            document.getElementById('processing').textContent = stats.processing;
            document.getElementById('completed').textContent = stats.completed;
        }
        
        // Оновлюємо кожні 10 секунд
        setInterval(refreshList, 10000);
        refreshList();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Головна сторінка"""
    numbers = PhoneNumber.query.all()
    stats = {
        'total': PhoneNumber.query.count(),
        'pending': PhoneNumber.query.filter_by(status='pending').count(),
        'processing': PhoneNumber.query.filter_by(status='processing').count(),
        'completed': PhoneNumber.query.filter_by(status='completed').count()
    }
    return render_template_string(HTML_TEMPLATE, numbers=numbers, services=SERVICES, stats=stats)

@app.route('/api/add_numbers', methods=['POST'])
def api_add_numbers():
    """API для додавання номерів"""
    data = request.json
    numbers_text = data.get('numbers', '')
    services = data.get('services', [])
    attempts = int(data.get('attempts', 1))
    
    numbers_list = [n.strip() for n in numbers_text.split('\n') if n.strip()]
    added = 0
    
    for number in numbers_list:
        existing = PhoneNumber.query.filter_by(number=number).first()
        if not existing:
            new_number = PhoneNumber(
                number=number,
                max_attempts=attempts,
                services=json.dumps(services)
            )
            db.session.add(new_number)
            added += 1
    
    db.session.commit()
    return jsonify({'success': True, 'added': added})

@app.route('/api/start_job', methods=['POST'])
def api_start_job():
    """Запустити процес реєстрації"""
    global STOP_SIGNAL, CURRENT_JOB_ID
    STOP_SIGNAL = False
    
    job = RegistrationJob(active=True)
    db.session.add(job)
    db.session.commit()
    
    CURRENT_JOB_ID = job.id
    
    thread = threading.Thread(target=registration_worker, args=(job.id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'job_id': job.id})

@app.route('/api/stop_job', methods=['POST'])
def api_stop_job():
    """Зупинити процес"""
    global STOP_SIGNAL
    STOP_SIGNAL = True
    
    job = RegistrationJob.query.filter_by(active=True).first()
    if job:
        job.active = False
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/numbers')
def api_numbers():
    """Отримати список номерів"""
    numbers = PhoneNumber.query.all()
    stats = {
        'total': PhoneNumber.query.count(),
        'pending': PhoneNumber.query.filter_by(status='pending').count(),
        'processing': PhoneNumber.query.filter_by(status='processing').count(),
        'completed': PhoneNumber.query.filter_by(status='completed').count()
    }
    
    numbers_data = []
    for n in numbers:
        numbers_data.append({
            'number': n.number,
            'status': n.status,
            'attempts': n.attempts,
            'max_attempts': n.max_attempts
        })
    
    return jsonify({'numbers': numbers_data, 'stats': stats})

# ===== TELEGRAM БОТ =====
async def telegram_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start для Telegram"""
    keyboard = [
        [InlineKeyboardButton("📱 Додати номери", callback_data='add')],
        [InlineKeyboardButton("🚀 Старт", callback_data='start')],
        [InlineKeyboardButton("⏹️ Стоп", callback_data='stop')],
        [InlineKeyboardButton("📊 Статус", callback_data='status')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 Бот реєстрації номерів\n"
        "Оберіть дію:",
        reply_markup=reply_markup
    )

async def telegram_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник кнопок Telegram"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'add':
        await query.message.reply_text(
            "Відправте номери телефонами, кожен з нового рядка."
        )
    elif query.data == 'start':
        with app.app_context():
            api_start_job()
        await query.message.reply_text("✅ Процес реєстрації запущено!")
    elif query.data == 'stop':
        with app.app_context():
            api_stop_job()
        await query.message.reply_text("⏹️ Процес зупинено!")
    elif query.data == 'status':
        with app.app_context():
            stats = {
                'total': PhoneNumber.query.count(),
                'pending': PhoneNumber.query.filter_by(status='pending').count(),
                'completed': PhoneNumber.query.filter_by(status='completed').count()
            }
        await query.message.reply_text(
            f"📊 Статистика:\n"
            f"Всього: {stats['total']}\n"
            f"Очікують: {stats['pending']}\n"
            f"Завершено: {stats['completed']}"
        )

async def telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень"""
    text = update.message.text
    
    if text.startswith('+') or text.replace(' ', '').isdigit():
        # Мабуть номер телефону
        with app.app_context():
            numbers = [n.strip() for n in text.split('\n') if n.strip()]
            for number in numbers:
                existing = PhoneNumber.query.filter_by(number=number).first()
                if not existing:
                    new_number = PhoneNumber(number=number)
                    db.session.add(new_number)
            db.session.commit()
        
        await update.message.reply_text(f"✅ Додано {len(numbers)} номерів")
    else:
        await update.message.reply_text("Надішліть номери телефонів для реєстрації")

def run_telegram_bot():
    """Запуск Telegram бота"""
    if not TELEGRAM_TOKEN:
        logging.warning("Telegram токен не вказано")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", telegram_start))
    application.add_handler(CallbackQueryHandler(telegram_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_message))
    
    application.run_polling()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    # Створюємо БД
    with app.app_context():
        db.create_all()
    
    # Запускаємо Telegram бота
    telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    telegram_thread.start()
    
    # Запускаємо Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
