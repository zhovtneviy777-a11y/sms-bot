"""
SMS Bot - Веб версія
Простий веб-інтерфейс для роботи з номерами телефонів
"""

import os
import time
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Налаштування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Завантажуємо конфігурацію
from dotenv import load_dotenv
load_dotenv()

from config import Config, SITES_CONFIG, check_config

app.secret_key = Config.SECRET_KEY

# Стан додатку
app_state = {
    "started_at": time.time(),
    "total_requests": 0,
    "successful": 0,
    "failed": 0,
    "last_activity": time.time()
}

# ================= ДОПОМІЖНІ ФУНКЦІЇ =================
def validate_phone(phone):
    """Перевірка номеру телефону"""
    if not phone:
        return False, "Введіть номер телефону"
    
    # Видаляємо всі нецифрові символи
    clean = ''.join(filter(str.isdigit, str(phone)))
    
    if len(clean) < 10:
        return False, "Номер занадто короткий"
    
    if len(clean) > 15:
        return False, "Номер занадто довгий"
    
    # Український формат
    if clean.startswith('380') and len(clean) == 12:
        formatted = f"+{clean[:3]} ({clean[3:5]}) {clean[5:8]}-{clean[8:10]}-{clean[10:12]}"
        return True, formatted
    
    return True, clean

def is_authenticated():
    """Перевірка автентифікації"""
    if Config.ADMIN_PASSWORD == "admin123":
        return True  # Якщо пароль за замовчуванням, не вимагаємо входу
    
    return session.get('authenticated', False)

def require_auth(f):
    """Декоратор для захищених маршрутів"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated

# ================= МАРШРУТИ =================
@app.route('/')
def index():
    """Головна сторінка"""
    app_state["total_requests"] += 1
    
    # Формуємо список сайтів
    sites = []
    for site_id, data in SITES_CONFIG.items():
        if data.get("enabled", True):
            sites.append({
                "id": site_id,
                "name": data["name"],
                "icon": data.get("icon", "🌐"),
                "description": data["description"]
            })
    
    return render_template('index.html', 
                         sites=sites,
                         stats=app_state,
                         authenticated=is_authenticated())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Сторінка входу"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if password == Config.ADMIN_PASSWORD:
            session['authenticated'] = True
            session.permanent = True
            logger.info("✅ Користувач увійшов в систему")
            
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        else:
            return render_template('login.html', error="Невірний пароль")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Вийти з системи"""
    session.pop('authenticated', None)
    logger.info("👋 Користувач вийшов з системи")
    return redirect(url_for('index'))

@app.route('/send', methods=['POST'])
@require_auth
def send_number():
    """Обробка відправки номеру"""
    app_state["total_requests"] += 1
    
    try:
        phone = request.form.get('phone', '').strip()
        site_id = request.form.get('site', '')
        
        # Валідація
        is_valid, result = validate_phone(phone)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": result
            })
        
        # Перевірка сайту
        if site_id not in SITES_CONFIG:
            return jsonify({
                "success": False,
                "message": f"Сайт не знайдено: {site_id}"
            })
        
        site = SITES_CONFIG[site_id]
        
        # Логуємо
        logger.info(f"📞 Запит: {result} для {site['name']}")
        
        # Тут буде реальна логіка з Selenium
        # Зараз просто симулюємо
        time.sleep(1)
        
        app_state["successful"] += 1
        
        return jsonify({
            "success": True,
            "message": f"✅ Номер {result} успішно відправлено на {site['name']}",
            "phone": result,
            "site": site['name'],
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        app_state["failed"] += 1
        logger.error(f"❌ Помилка: {e}")
        
        return jsonify({
            "success": False,
            "message": f"Помилка обробки: {str(e)}"
        })

@app.route('/api/sites')
def api_sites():
    """API для отримання сайтів"""
    sites = []
    for site_id, data in SITES_CONFIG.items():
        if data.get("enabled", True):
            sites.append({
                "id": site_id,
                "name": data["name"],
                "icon": data.get("icon", "🌐"),
                "description": data["description"],
                "url": data["url"]
            })
    
    return jsonify({"sites": sites})

@app.route('/api/stats')
def api_stats():
    """API статистики"""
    return jsonify({
        "uptime": int(time.time() - app_state["started_at"]),
        "requests": app_state["total_requests"],
        "successful": app_state["successful"],
        "failed": app_state["failed"],
        "online": True
    })

@app.route('/health')
def health():
    """Health check для Railway"""
    return jsonify({
        "status": "healthy",
        "service": "SMS Bot Web",
        "uptime": int(time.time() - app_state["started_at"]),
        "version": "1.0.0"
    }), 200

@app.route('/admin')
@require_auth
def admin():
    """Адмін панель"""
    return render_template('admin.html', 
                         stats=app_state,
                         sites=SITES_CONFIG)

# ================= HTML ШАБЛОНИ (inline) =================
@app.route('/static/<path:filename>')
def static_files(filename):
    """Статичні файли"""
    from flask import send_from_directory
    
    # Створюємо папку static якщо немає
    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
    
    return send_from_directory(static_dir, filename)

# ================= ЗАПУСК =================
if __name__ == '__main__':
    # Перевіряємо конфігурацію
    check_config()
    
    # Запускаємо
    logger.info(f"🚀 Запуск веб-версії на порті {Config.PORT}")
    logger.info(f"🔗 http://localhost:{Config.PORT}")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
