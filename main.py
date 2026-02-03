"""
SMS Bot - Веб версія для Railway
"""

import os
import time
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Конфігурація з Railway змінних
app.secret_key = os.getenv("SECRET_KEY", "railway-secret-key")
PORT = int(os.getenv("PORT", 8000))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Сайти для обробки
SITES = {
    "OLX.ua": {"icon": "🛒", "desc": "Оголошення та продажі"},
    "Rozetka.com.ua": {"icon": "💻", "desc": "Інтернет-магазин"},
    "Prom.ua": {"icon": "📦", "desc": "Маркетплейс"},
    "NovaPoshta": {"icon": "🚚", "desc": "Служба доставки"},
    "EpicentrK.ua": {"icon": "🏠", "desc": "Будівельний магазин"}
}

# Стан додатку
stats = {
    "started_at": time.time(),
    "requests": 0,
    "success": 0,
    "errors": 0
}

# Перевірка автентифікації
def is_authenticated():
    return session.get('authenticated', False)

# HTML шаблон головної сторінки
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 SMS Bot - Railway</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
        }
        .tagline {
            text-align: center;
            opacity: 0.8;
            margin-bottom: 30px;
        }
        .auth-buttons {
            position: absolute;
            top: 20px;
            right: 20px;
        }
        .btn {
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            color: white;
        }
        .btn-primary {
            background: #4CAF50;
            width: 100%;
            padding: 12px;
            font-size: 16px;
        }
        .sites-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .site-card {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .site-icon {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
        }
        .success { background: rgba(76, 175, 80, 0.2); }
        .error { background: rgba(244, 67, 54, 0.2); }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            text-align: center;
        }
        .stat-item {
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            min-width: 120px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="auth-buttons">
            {% if authenticated %}
                <a href="/logout" class="btn">🚪 Вийти</a>
            {% else %}
                <a href="/login" class="btn">🔐 Увійти</a>
            {% endif %}
        </div>
        
        <h1>📱 SMS Bot</h1>
        <p class="tagline">Веб-версія на Railway</p>
        
        <div class="form-group">
            <label>📞 Номер телефону:</label>
            <input type="text" id="phone" placeholder="380501234567">
        </div>
        
        <div class="form-group">
            <label>🌐 Виберіть сайт:</label>
            <select id="site">
                <option value="">-- Оберіть --</option>
                {% for site_id, site in sites.items() %}
                <option value="{{ site_id }}">{{ site.icon }} {{ site_id }}</option>
                {% endfor %}
            </select>
        </div>
        
        <button onclick="sendNumber()" class="btn btn-primary"
                {% if not authenticated %}disabled{% endif %}>
            📨 Відправити номер
        </button>
        
        {% if not authenticated %}
        <p style="text-align:center; margin-top:10px;">
            🔒 <a href="/login" style="color:#4CAF50;">Увійдіть</a> для відправки
        </p>
        {% endif %}
        
        <div id="result" class="result"></div>
        
        <h3>🌐 Доступні сайти</h3>
        <div class="sites-grid">
            {% for site_id, site in sites.items() %}
            <div class="site-card">
                <div class="site-icon">{{ site.icon }}</div>
                <div><strong>{{ site_id }}</strong></div>
                <div style="font-size:12px;">{{ site.desc }}</div>
            </div>
            {% endfor %}
        </div>
        
        <h3>📊 Статистика</h3>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="uptime">0</div>
                <div>секунд</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{ stats.requests }}</div>
                <div>запитів</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{ stats.success }}</div>
                <div>успішно</div>
            </div>
        </div>
        
        <footer>
            <p>🚀 Працює на Railway | <a href="/health" style="color:#4CAF50;">Health Check</a></p>
            <p>Порт: {{ port }} | Аптайм: <span id="uptime2">0</span> сек</p>
        </footer>
    </div>
    
    <script>
        // Оновлення аптайму
        function updateUptime() {
            const uptime = Math.floor((Date.now() / 1000) - {{ start_time }});
            document.getElementById('uptime').textContent = uptime;
            document.getElementById('uptime2').textContent = uptime;
        }
        setInterval(updateUptime, 1000);
        updateUptime();
        
        // Відправка номера
        async function sendNumber() {
            const phone = document.getElementById('phone').value;
            const site = document.getElementById('site').value;
            const result = document.getElementById('result');
            
            if (!phone || !site) {
                result.className = 'result error';
                result.innerHTML = '❌ Заповніть всі поля';
                result.style.display = 'block';
                return;
            }
            
            result.className = 'result';
            result.innerHTML = '⏳ Обробляємо...';
            result.style.display = 'block';
            
            try {
                const response = await fetch('/api/send', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: phone, site: site})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    result.className = 'result success';
                    result.innerHTML = `✅ ${data.message}`;
                    location.reload(); // Оновити статистику
                } else {
                    result.className = 'result error';
                    result.innerHTML = `❌ ${data.message}`;
                }
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = '❌ Помилка мережі';
            }
        }
        
        // Автоформат телефону
        document.getElementById('phone').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.startsWith('380') && value.length === 12) {
                value = `+${value.slice(0,3)} (${value.slice(3,5)}) ${value.slice(5,8)}-${value.slice(8,10)}-${value.slice(10,12)}`;
            }
            e.target.value = value;
        });
    </script>
</body>
</html>
'''

# HTML шаблон входу
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔐 Вхід - SMS Bot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .login-box {
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 15px;
            width: 100%;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            color: white;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        .error {
            color: #ff6b6b;
            text-align: center;
            margin-bottom: 15px;
        }
        .back {
            text-align: center;
            margin-top: 20px;
        }
        a {
            color: #4CAF50;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 Вхід в систему</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <input type="password" name="password" placeholder="Пароль" required autofocus>
            <button type="submit">Увійти</button>
        </form>
        
        <div class="back">
            <a href="/">← На головну</a>
        </div>
    </div>
</body>
</html>
'''

# ==================== МАРШРУТИ ====================
@app.route('/')
def index():
    """Головна сторінка"""
    stats["requests"] += 1
    return render_template_string(INDEX_HTML, 
                                sites=SITES,
                                stats=stats,
                                authenticated=is_authenticated(),
                                port=PORT,
                                start_time=stats["started_at"])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Сторінка входу"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect('/')
        return render_template_string(LOGIN_HTML, error="Невірний пароль")
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    """Вийти"""
    session.pop('authenticated', None)
    return redirect('/')

@app.route('/api/send', methods=['POST'])
def api_send():
    """API для відправки"""
    if not is_authenticated():
        return jsonify({"success": False, "message": "Потрібно увійти"})
    
    try:
        data = request.json
        phone = data.get('phone', '')
        site = data.get('site', '')
        
        # Валідація
        if not phone or not site:
            return jsonify({"success": False, "message": "Заповніть всі поля"})
        
        if site not in SITES:
            return jsonify({"success": False, "message": "Невідомий сайт"})
        
        # Симуляція обробки
        import time
        time.sleep(1)
        
        stats["success"] += 1
        
        return jsonify({
            "success": True,
            "message": f"Номер відправлено на {site}",
            "phone": phone,
            "site": site
        })
        
    except Exception as e:
        stats["errors"] += 1
        return jsonify({"success": False, "message": str(e)})

@app.route('/health')
def health():
    """Health check для Railway"""
    return jsonify({
        "status": "healthy",
        "service": "SMS Bot Web",
        "uptime": int(time.time() - stats["started_at"]),
        "requests": stats["requests"],
        "version": "1.0"
    })

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    logger.info(f"🚀 Запуск веб-версії на порті {PORT}")
    logger.info(f"🔗 Домен: https://sms-bot-production-4260.up.railway.app")
    logger.info(f"🔒 Пароль: {'Встановлено' if ADMIN_PASSWORD != 'admin123' else 'За замовчуванням'}")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
