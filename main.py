from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import threading
import time
import os

app = Flask(__name__)

# Глобальна змінна для драйвера
driver = None
driver_ready = False

def init_selenium():
    """Ініціалізує Selenium в окремому потоці"""
    global driver, driver_ready
    
    try:
        print("🔄 Ініціалізація Selenium...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Новий headless режим
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Автоматичний шлях до ChromeDriver через webdriver-manager
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Проста перевірка роботи
        driver.get("about:blank")
        
        driver_ready = True
        print("✅ Selenium успішно ініціалізовано")
        
    except Exception as e:
        print(f"❌ Помилка ініціалізації Selenium: {str(e)}")
        driver_ready = False

@app.route('/health')
def health():
    """Healthcheck ендпоінт"""
    if driver_ready:
        return jsonify({
            "status": "healthy",
            "selenium": "ready",
            "timestamp": time.time()
        }), 200
    else:
        return jsonify({
            "status": "initializing",
            "selenium": "not_ready",
            "timestamp": time.time()
        }), 503  # Service Unavailable - ще не готовий

@app.route('/')
def home():
    return jsonify({
        "message": "Selenium Flask App",
        "selenium_ready": driver_ready
    })

@app.route('/test-selenium')
def test_selenium():
    """Тестовий маршрут для перевірки Selenium"""
    if not driver_ready:
        return jsonify({"error": "Selenium не готовий"}), 503
    
    try:
        driver.get("https://httpbin.org/html")
        title = driver.title
        return jsonify({
            "success": True,
            "title": title,
            "url": driver.current_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_selenium_thread():
    """Запускає Selenium в окремому потоці"""
    selenium_thread = threading.Thread(target=init_selenium, daemon=True)
    selenium_thread.start()

if __name__ == '__main__':
    # Запускаємо Selenium у фоні
    start_selenium_thread()
    
    # Запускаємо Flask
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
