import os
import json
import time
import threading
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ===== НАЛАШТУВАНЯ ЛОГУВАННЯ =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== FLASK І БАЗА ДАНИХ =====
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///numbers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===== МОДЕЛІ =====
class PhoneNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=1)
    services = db.Column(db.Text, default='[]')
    results = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.now)

class RegistrationJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=False)
    total_numbers = db.Column(db.Integer, default=0)
    completed = db.Column(db.Integer, default=0)
    failed = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime)
    stopped_at = db.Column(db.DateTime)

# ===== ГЛОБАЛЬНІ ЗМІННІ =====
stop_signal = False
current_job = None

# ===== СЕРВІСИ ДЛЯ РЕЄСТРАЦІЇ =====
SERVICES_CONFIG = {
    'olx': {
        'name': 'OLX',
        'url': 'https://www.olx.ua/account/register/',
        'fields': {'phone': 'phone', 'email': 'email', 'password': 'password'}
    },
    'amazon': {
        'name': 'Amazon',
        'url': 'https://www.amazon.com/ap/register',
        'fields': {'name': 'ap_customer_name', 'email': 'ap_email', 'password': 'ap_password'}
    },
    'ebay': {
        'name': 'eBay',
        'url': 'https://signup.ebay.com/pa/crte',
        'fields': {'email': 'email', 'password': 'password'}
    },
    'paypal': {
        'name': 'PayPal',
        'url': 'https://www.paypal.com/signup',
        'fields': {'email': 'email', 'password': 'password'}
    },
    'google': {
        'name': 'Google',
        'url': 'https://accounts.google.com/signup',
        'fields': {'email': 'email', 'password': 'password'}
    },
    'microsoft': {
        'name': 'Microsoft',
        'url': 'https://signup.live.com/',
        'fields': {'email': 'MemberName', 'password': 'Password'}
    },
    'whatsapp': {
        'name': 'WhatsApp',
        'url': 'https://www.whatsapp.com/download',
        'fields': {'phone': 'phone'}
    }
}

# ===== SELENIUM УТІЛІТИ =====
def create_driver():
    """Створення драйвера з налаштуваннями для Render"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Для Render
    if os.environ.get('CHROME_BIN'):
        chrome_options.binary_location = os.environ.get('CHROME_BIN')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def generate_email(phone):
    """Генерація унікального email на основі номера"""
    timestamp = int(time.time())
    return f"user{timestamp}_{phone[-4:]}@temp-mail.com"

def generate_password():
    """Генерація безпечного пароля"""
    import random
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(12))

# ===== ФУНКЦІЇ РЕЄСТРАЦІЇ =====
def register_on_service(service_id, phone_number):
    """Загальна функція реєстрації"""
    if service_id not in SERVICES_CONFIG:
        return {"success": False, "error": "Невідомий сервіс"}
    
    service = SERVICES_CONFIG[service_id]
    driver = None
    
    try:
        driver = create_driver()
        driver.get(service['url'])
        time.sleep(3)  # Чекаємо завантаження
        
        # Генеруємо дані для реєстрації
        email = generate_email(phone_number)
        password = generate_password()
        
        results = {"service": service['name'], "phone": phone_number, "steps": []}
        
        # Заповнюємо поля форми
        for field_type, field_name in service['fields'].items():
            try:
                if field_type == 'phone':
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, field_name))
                    )
                    element.clear()
                    element.send_keys(phone_number)
                    results['steps'].append(f"Поле {field_type} заповнено")
                    
                elif field_type in ['email', 'name']:
                    element = driver.find_element(By.NAME, field_name)
                    element.clear()
                    if field_type == 'email':
                        element.send_keys(email)
                    else:
                        element.send_keys("Test User")
                    results['steps'].append(f"Поле {field_type} заповнено")
                    
                elif field_type == 'password':
                    element = driver.find_element(By.NAME, field_name)
                    element.clear()
                    element.send_keys(password)
                    results['steps'].append(f"Поле {field_type} заповнено")
                    
            except (NoSuchElementException, TimeoutException) as e:
                results['steps'].append(f"Поле {field_type} не знайдено: {str(e)}")
                continue
        
        # Намагаємося знайти кнопку відправки
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:contains('Продовжити')",
            "button:contains('Continue')",
            "button:contains('Реєстрація')",
            "button:contains('Register')"
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                if 'contains' in selector:
                    import re
                    text = re.search(r"contains\('(.*?)'\)", selector).group(1)
                    elements = driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    if elements:
                        elements[0].click()
                        submitted = True
                        break
                else:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                    submitted = True
                    break
            except:
                continue
        
        if submitted:
            results['steps'].append("Форма відправлена")
            time.sleep(5)  # Чекаємо відповіді сервера
            
            # Перевіряємо чи є повідомлення про SMS
            sms_indicators = ["SMS", "смс", "код", "code", "verify", "підтвердити"]
            page_text = driver.page_source.lower()
            
            if any(indicator in page_text for indicator in sms_indicators):
                results['success'] = True
                results['message'] = "Очікуємо SMS код"
                results['data'] = {"email": email, "password": password}
            else:
                results['success'] = True
                results['message'] = "Форма оброблена"
                results['data'] = {"email": email, "password": password}
        else:
            results['success'] = False
            results['error'] = "Не вдалося знайти кнопку відправки"
        
        return results
        
    except Exception as e:
        return {"success": False, "error": str(e), "service": service['name']}
    
    finally:
        if driver:
            driver.quit()

# ===== РОБОЧИЙ ПРОЦЕС =====
def registration_worker():
    """Фоновий процес реєстрації номерів"""
    global stop_signal, current_job
    
    with app.app_context():
        # Створюємо нове завдання
        job = RegistrationJob(
            is_active=True,
            total_numbers=PhoneNumber.query.filter_by(status='pending').count(),
            started_at=datetime.now()
        )
        db.session.add(job)
        db.session.commit()
        current_job = job.id
        
        logger.info(f"Запуск завдання #{job.id} з {job.total_numbers} номерами")
        
        while not stop_signal and job.is_active:
            # Беремо наступний номер
            number = PhoneNumber.query.filter_by(status='pending').first()
            if not number:
                logger.info("Немає номерів для обробки")
                break
            
            # Оновлюємо статус
            number.status = 'processing'
            db.session.commit()
            
            # Отримуємо сервіси для цього номера
            services = json.loads(number.services)
            all_results = {}
            
            logger.info(f"Обробка {number.number} на {len(services)} сервісах")
            
            # Реєструємо на кожному сервісі
            for service_id in services:
                if stop_signal:
                    break
                
                logger.info(f"Реєстрація {number.number} на {service_id}")
                result = register_on_service(service_id, number.number)
                all_results[service_id] = result
                
                number.attempts += 1
                
                # Пауза між сервісами
                if not stop_signal:
                    time.sleep(5)
            
            # Зберігаємо результати
            number.results = json.dumps(all_results)
            
            # Перевіряємо успішність
            success_count = sum(1 for r in all_results.values() if r.get('success'))
            if success_count > 0:
                number.status = 'completed'
                job.completed += 1
            else:
                number.status = 'failed'
                job.failed += 1
            
            db.session.commit()
            
            # Пауза між номерами
            if not stop_signal:
                time.sleep(10)
        
        # Завершення роботи
        job.is_active = False
        job.stopped_at = datetime.now()
        db.session.commit()
        current_job = None
        logger.info(f"Завдання #{job.id} завершено")

# ===== ВЕБ-ІНТЕРФЕЙС =====
@app.route('/')
def index():
    """Головна сторінка"""
    numbers = PhoneNumber.query.order_by(PhoneNumber.created_at.desc()).limit(50).all()
    jobs = RegistrationJob.query.order_by(RegistrationJob.started_at.desc()).limit(5).all()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Реєстратор номерів</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .section { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 10px; }
            textarea { width: 100%; height: 150px; padding: 10px; border: 1px solid #ddd; }
            input[type="number"] { width: 60px; padding: 5px; }
            button { background: #007bff; color: white; border: none; padding: 10px 20px; 
                     margin: 5px; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .btn-stop { background: #dc3545; }
            .btn-stop:hover { background: #c82333; }
            .service-list { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }
            .service-item { background: white; padding: 10px; border-radius: 5px; border: 1px solid #ddd; }
            .numbers-list { max-height: 400px; overflow-y: auto; }
            .number-item { padding: 8px; border-bottom: 1px solid #eee; }
            .status-pending { color: #ffc107; }
            .status-processing { color: #17a2b8; }
            .status-completed { color: #28a745; }
            .status-failed { color: #dc3545; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat-item { background: white; padding: 15px; border-radius: 5px; text-align: center; }
        </style>
    </head>
    <body>
        <h1>🤖 Реєстратор номерів</h1>
        
        <div class="section">
            <h2>📱 Додати номери</h2>
            <textarea id="numbersInput" placeholder="Введіть номери (кожен з нового рядка):
+380111111111
+380222222222"></textarea>
            
            <h3>Оберіть сервіси:</h3>
            <div class="service-list" id="servicesList">
    '''
    
    for service_id, config in SERVICES_CONFIG.items():
        html += f'''
                <label class="service-item">
                    <input type="checkbox" name="service" value="{service_id}" checked>
                    {config['name']}
                </label>
        '''
    
    html += '''
            </div>
            
            <div>
                <label>Кількість спроб: </label>
                <input type="number" id="attemptsInput" value="1" min="1" max="10">
            </div>
            
            <button onclick="addNumbers()">✅ Додати номери</button>
        </div>
        
        <div class="section">
            <h2>🚀 Керування</h2>
            <button onclick="startRegistration()">▶️ Почати реєстрацію</button>
            <button class="btn-stop" onclick="stopRegistration()">⏹️ Зупинити</button>
            
            <div class="stats">
                <div class="stat-item">
                    <h3>Всього</h3>
                    <div id="totalCount">0</div>
                </div>
                <div class="stat-item">
                    <h3>Очікують</h3>
                    <div id="pendingCount">0</div>
                </div>
                <div class="stat-item">
                    <h3>Виконуються</h3>
                    <div id="processingCount">0</div>
                </div>
                <div class="stat-item">
                    <h3>Завершено</h3>
                    <div id="completedCount">0</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Останні номери</h2>
            <div class="numbers-list" id="numbersList">
    '''
    
    for number in numbers:
        html += f'''
                <div class="number-item status-{number.status}">
                    {number.number} - {number.status} ({number.attempts}/{number.max_attempts})
                </div>
        '''
    
    html += '''
            </div>
            <button onclick="refreshData()">🔄 Оновити</button>
        </div>
        
        <script>
            function addNumbers() {
                const numbers = document.getElementById('numbersInput').value;
                const checkboxes = document.querySelectorAll('#servicesList input[type="checkbox"]:checked');
                const services = Array.from(checkboxes).map(cb => cb.value);
                const attempts = document.getElementById('attemptsInput').value;
                
                fetch('/api/numbers', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({numbers, services, attempts})
                })
                .then(r => r.json())
                .then(data => {
                    alert(`Додано ${data.added} номерів`);
                    refreshData();
                });
            }
            
            function startRegistration() {
                fetch('/api/start', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    refreshData();
                });
            }
            
            function stopRegistration() {
                fetch('/api/stop', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    refreshData();
                });
            }
            
            function refreshData() {
                fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    // Оновлюємо статистику
                    document.getElementById('totalCount').textContent = data.total;
                    document.getElementById('pendingCount').textContent = data.pending;
                    document.getElementById('processingCount').textContent = data.processing;
                    document.getElementById('completedCount').textContent = data.completed;
                    
                    // Оновлюємо список номерів
                    let numbersHtml = '';
                    data.numbers.forEach(n => {
                        numbersHtml += `<div class="number-item status-${n.status}">${n.number} - ${n.status} (${n.attempts}/${n.max_attempts})</div>`;
                    });
                    document.getElementById('numbersList').innerHTML = numbersHtml;
                });
            }
            
            // Автооновлення кожні 10 секунд
            setInterval(refreshData, 10000);
            refreshData();
        </script>
    </body>
    </html>
    '''
    
    return html

# ===== API =====
@app.route('/api/numbers', methods=['POST'])
def api_add_numbers():
    """Додати номери"""
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

@app.route('/api/start', methods=['POST'])
def api_start():
    """Почати реєстрацію"""
    global stop_signal, current_job
    
    if current_job:
        return jsonify({'success': False, 'message': 'Завдання вже виконується'})
    
    stop_signal = False
    thread = threading.Thread(target=registration_worker, daemon=True)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Реєстрацію запущено'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Зупинити реєстрацію"""
    global stop_signal
    
    stop_signal = True
    return jsonify({'success': True, 'message': 'Зупинено'})

@app.route('/api/stats')
def api_stats():
    """Статистика"""
    total = PhoneNumber.query.count()
    pending = PhoneNumber.query.filter_by(status='pending').count()
    processing = PhoneNumber.query.filter_by(status='processing').count()
    completed = PhoneNumber.query.filter_by(status='completed').count()
    
    numbers = PhoneNumber.query.order_by(PhoneNumber.created_at.desc()).limit(20).all()
    numbers_data = []
    
    for n in numbers:
        numbers_data.append({
            'number': n.number,
            'status': n.status,
            'attempts': n.attempts,
            'max_attempts': n.max_attempts
        })
    
    return jsonify({
        'total': total,
        'pending': pending,
        'processing': processing,
        'completed': completed,
        'numbers': numbers_data
    })

@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Очистити базу даних"""
    PhoneNumber.query.delete()
    RegistrationJob.query.delete()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Базу очищено'})

# ===== ЗАПУСК =====
def init_database():
    """Ініціалізація бази даних"""
    with app.app_context():
        db.create_all()
        logger.info("База даних ініціалізована")

if __name__ == "__main__":
    # Ініціалізуємо базу даних
    init_database()
    
    # Запускаємо Flask
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Запуск Flask на порті {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
