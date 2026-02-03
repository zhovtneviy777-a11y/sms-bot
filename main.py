"""
SMS Bot - Система реєстрації телефонних номерів
"""

import os
import json
import time
from flask import Flask, render_template_string, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "railway-secret-123")

# База даних у пам'яті (для демо)
phones_database = []
STATS_FILE = "phones_data.json"

# Сайти для демонстрації
SITES = {
    "OLX.ua": "🛒",
    "Rozetka.com.ua": "💻", 
    "Prom.ua": "📦",
    "NovaPoshta": "🚚",
    "EpicentrK.ua": "🏠"
}

# Статистика
stats = {"started_at": time.time(), "requests": 0, "phones_registered": 0}

def load_phones():
    """Завантажити номери з файлу"""
    global phones_database
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                phones_database = json.load(f)
                stats["phones_registered"] = len(phones_database)
    except:
        phones_database = []

def save_phones():
    """Зберегти номери у файл"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(phones_database, f, ensure_ascii=False, indent=2)
    except:
        pass

# Завантажити дані при старті
load_phones()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>📱 SMS Bot - Реєстрація номерів</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        
        h1 {
            color: #4a5568;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #718096;
            font-size: 1.2rem;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .card h2 {
            color: #4a5568;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4a5568;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 25px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-delete {
            background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
        }
        
        .btn-export {
            background: linear-gradient(135deg, #48bb78 0%, #2f855a 100%);
        }
        
        .phones-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .phone-item {
            background: #f7fafc;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        
        .phone-item:nth-child(odd) {
            background: #edf2f7;
        }
        
        .phone-number {
            font-weight: bold;
            font-size: 1.1rem;
            color: #2d3748;
        }
        
        .phone-meta {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            color: #718096;
            font-size: 0.9rem;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #a0aec0;
        }
        
        .empty-state i {
            font-size: 3rem;
            margin-bottom: 15px;
            opacity: 0.5;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .alert-success {
            background: #c6f6d5;
            color: #22543d;
            border-left: 4px solid #48bb78;
        }
        
        .alert-error {
            background: #fed7d7;
            color: #742a2a;
            border-left: 4px solid #f56565;
        }
        
        .sites-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .site-card {
            background: #edf2f7;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .site-card:hover {
            transform: translateY(-3px);
        }
        
        .site-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .site-name {
            font-weight: 600;
            color: #4a5568;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📱 SMS Bot - Реєстрація номерів</h1>
            <p class="subtitle">Система зберігання та керування телефонними номерами</p>
        </header>
        
        {% if message %}
        <div class="alert alert-{{ message_type }}">
            {{ message_icon }} {{ message }}
        </div>
        {% endif %}
        
        <div class="main-content">
            <!-- Форма реєстрації -->
            <div class="card">
                <h2>📝 Реєстрація нового номера</h2>
                <form method="POST" action="/register">
                    <div class="form-group">
                        <label for="phone">📱 Номер телефону</label>
                        <input type="tel" id="phone" name="phone" 
                               placeholder="+380XXXXXXXXX" 
                               pattern="^\+?[0-9\s\-\(\)]+$"
                               required>
                    </div>
                    
                    <div class="form-group">
                        <label for="name">👤 Ім'я власника (необов'язково)</label>
                        <input type="text" id="name" name="name" 
                               placeholder="Володимир">
                    </div>
                    
                    <div class="form-group">
                        <label for="notes">📝 Примітки (необов'язково)</label>
                        <textarea id="notes" name="notes" 
                                  placeholder="Додаткові відомості про номер..."></textarea>
                    </div>
                    
                    <button type="submit" class="btn">
                        ✅ Зареєструвати номер
                    </button>
                </form>
                
                <div style="margin-top: 30px;">
                    <h3>🌐 Доступні сайти для моніторингу:</h3>
                    <div class="sites-grid">
                        {% for site, icon in sites.items() %}
                        <div class="site-card">
                            <div class="site-icon">{{ icon }}</div>
                            <div class="site-name">{{ site }}</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Список зареєстрованих номерів -->
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>📋 Зареєстровані номери</h2>
                    <div style="display: flex; gap: 10px;">
                        <a href="/export" class="btn btn-export" target="_blank">
                            📥 Експорт JSON
                        </a>
                        {% if phones %}
                        <form method="POST" action="/clear" style="display: inline;">
                            <button type="submit" class="btn btn-delete" 
                                    onclick="return confirm('Видалити всі номери?')">
                                🗑️ Очистити
                            </button>
                        </form>
                        {% endif %}
                    </div>
                </div>
                
                <div class="phones-list">
                    {% if phones %}
                        {% for phone in phones %}
                        <div class="phone-item">
                            <div class="phone-number">📱 {{ phone.phone }}</div>
                            {% if phone.name %}
                            <div style="margin-top: 5px;">
                                👤 <strong>{{ phone.name }}</strong>
                            </div>
                            {% endif %}
                            {% if phone.notes %}
                            <div style="margin-top: 5px; color: #4a5568;">
                                📝 {{ phone.notes }}
                            </div>
                            {% endif %}
                            <div class="phone-meta">
                                <span>🕒 {{ phone.timestamp }}</span>
                                <form method="POST" action="/delete/{{ loop.index0 }}" 
                                      style="display: inline;">
                                    <button type="submit" class="btn btn-delete" 
                                            style="padding: 5px 10px; font-size: 12px;">
                                        Видалити
                                    </button>
                                </form>
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div class="empty-state">
                            <div>📭</div>
                            <h3>Немає зареєстрованих номерів</h3>
                            <p>Додайте перший номер телефону</p>
                        </div>
                    {% endif %}
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <p>Всього номерів: <strong>{{ phones|length }}</strong></p>
                </div>
            </div>
        </div>
        
        <!-- Статистика -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">🕒 Час роботи</div>
                <div class="stat-value" id="uptime">0</div>
                <div class="stat-label">секунд</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">📊 Запитів</div>
                <div class="stat-value">{{ stats.requests }}</div>
                <div class="stat-label">всього</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">📱 Номерів</div>
                <div class="stat-value">{{ phones|length }}</div>
                <div class="stat-label">зареєстровано</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">🌐 Сайтів</div>
                <div class="stat-value">{{ sites|length }}</div>
                <div class="stat-label">для моніторингу</div>
            </div>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #718096;">
            <p>🚀 SMS Bot на Railway | Реєстрація телефонних номерів | Версія 2.0</p>
            <p style="margin-top: 10px;">
                <a href="/health" style="color: #4299e1; text-decoration: none;">🔧 Health Check</a> |
                <a href="/api/phones" style="color: #4299e1; text-decoration: none;">📡 API</a> |
                <a href="/" style="color: #4299e1; text-decoration: none;">🔄 Оновити</a>
            </p>
        </footer>
    </div>
    
    <script>
        // Оновлення часу роботи
        setInterval(() => {
            document.getElementById('uptime').textContent = 
                Math.floor((Date.now()/1000) - {{ stats.started_at }});
        }, 1000);
        
        // Автоформатування номера телефону
        document.getElementById('phone').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (!value.startsWith('380')) {
                    value = '380' + value;
                }
                e.target.value = '+' + value;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    stats["requests"] += 1
    return render_template_string(HTML_TEMPLATE, 
                                 phones=phones_database,
                                 sites=SITES,
                                 stats=stats,
                                 message=request.args.get('message'),
                                 message_type=request.args.get('type', 'success'),
                                 message_icon=request.args.get('icon', '✅'))

@app.route('/register', methods=['POST'])
def register_phone():
    """Реєстрація нового телефонного номера"""
    phone = request.form.get('phone', '').strip()
    name = request.form.get('name', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if not phone:
        return redirect(url_for('home', 
                               message='Помилка: номер телефону обовʼязковий',
                               type='error',
                               icon='❌'))
    
    # Перевірка, чи номер вже існує
    for existing in phones_database:
        if existing['phone'] == phone:
            return redirect(url_for('home',
                                   message=f'Номер {phone} вже зареєстрований',
                                   type='error',
                                   icon='⚠️'))
    
    # Додати новий номер
    new_phone = {
        'phone': phone,
        'name': name if name else None,
        'notes': notes if notes else None,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'registered_at': time.time()
    }
    
    phones_database.append(new_phone)
    stats["phones_registered"] = len(phones_database)
    save_phones()
    
    return redirect(url_for('home',
                           message=f'Номер {phone} успішно зареєстровано!',
                           type='success',
                           icon='✅'))

@app.route('/delete/<int:index>', methods=['POST'])
def delete_phone(index):
    """Видалити номер за індексом"""
    if 0 <= index < len(phones_database):
        deleted_phone = phones_database.pop(index)
        stats["phones_registered"] = len(phones_database)
        save_phones()
        return redirect(url_for('home',
                               message=f'Номер {deleted_phone["phone"]} видалено',
                               type='success',
                               icon='🗑️'))
    return redirect(url_for('home',
                           message='Номер не знайдено',
                           type='error',
                           icon='❌'))

@app.route('/clear', methods=['POST'])
def clear_all():
    """Очистити всі номери"""
    phones_database.clear()
    stats["phones_registered"] = 0
    save_phones()
    return redirect(url_for('home',
                           message='Всі номери видалено',
                           type='success',
                           icon='🗑️'))

@app.route('/export')
def export_phones():
    """Експорт номерів у форматі JSON"""
    return jsonify({
        "status": "success",
        "count": len(phones_database),
        "phones": phones_database,
        "exported_at": time.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/phones')
def api_phones():
    """API для отримання списку номерів"""
    return jsonify(phones_database)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "SMS Bot - Phone Registry",
        "uptime": int(time.time() - stats["started_at"]),
        "requests": stats["requests"],
        "phones_registered": stats["phones_registered"],
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Запуск SMS Bot Phone Registry на порті {port}")
    print(f"📱 Зареєстровано номерів: {stats['phones_registered']}")
    app.run(host='0.0.0.0', port=port, debug=False)
