"""
SMS Bot - Проста веб-версія для Railway
БЕЗ Selenium, тільки Flask
"""

import os
import time
from flask import Flask, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "railway-secret-123")

# Сайти
SITES = {
    "OLX.ua": "🛒",
    "Rozetka.com.ua": "💻", 
    "Prom.ua": "📦",
    "NovaPoshta": "🚚",
    "EpicentrK.ua": "🏠"
}

# Статистика
stats = {"started_at": time.time(), "requests": 0}

@app.route('/')
def home():
    stats["requests"] += 1
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📱 SMS Bot - Railway</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
            }
            h1 { margin-bottom: 20px; }
            .sites {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 15px;
                margin: 30px 0;
            }
            .site {
                background: rgba(255,255,255,0.2);
                padding: 15px;
                border-radius: 10px;
                min-width: 150px;
            }
            .stats {
                margin-top: 30px;
                padding: 20px;
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 SMS Bot - Веб версія</h1>
            <p>Працює на Railway без Selenium</p>
            
            <div class="sites">
                <h3>🌐 Доступні сайти:</h3>
                ''' + ''.join([f'<div class="site">{icon} {name}</div>' 
                               for name, icon in SITES.items()]) + '''
            </div>
            
            <div class="stats">
                <h3>📊 Статистика</h3>
                <p>Запущено: <span id="uptime">0</span> секунд тому</p>
                <p>Запитів: ''' + str(stats["requests"]) + '''</p>
                <p><a href="/health" style="color:#4CAF50;">Health Check</a></p>
            </div>
            
            <p style="margin-top: 40px; opacity: 0.8;">
                Версія без Selenium | Railway 🚀
            </p>
        </div>
        
        <script>
            setInterval(() => {
                document.getElementById('uptime').textContent = 
                    Math.floor((Date.now()/1000) - ''' + str(stats["started_at"]) + ''');
            }, 1000);
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "SMS Bot Web (No Selenium)",
        "uptime": int(time.time() - stats["started_at"]),
        "requests": stats["requests"]
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Запуск на Railway (порт {port})")
    app.run(host='0.0.0.0', port=port)
