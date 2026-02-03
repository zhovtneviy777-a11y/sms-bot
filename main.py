# ЗМІНІТЬ це у main.py:

from flask import Flask, jsonify
import threading
import time
import os

app = Flask(__name__)
driver_ready = False
driver = None

def init_selenium():
    global driver, driver_ready
    
    try:
        print("🤖 Запускаємо Selenium для бота реєстрації номерів...")
        time.sleep(5)  # Чекаємо на системні залежності
        
        # ВИДАЛИТЬ webdriver-manager - він не працює в контейнері!
        # ЗАМІСТЬ цього:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # ВАЖЛИВО: Використовуємо системний chromedriver
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Простий тест
        driver.get("about:blank")
        print(f"✅ Chrome запущено: {driver.title}")
        
        driver_ready = True
        print("🎉 Selenium готовий до роботи з номерами!")
        
    except Exception as e:
        print(f"🔥 КРИТИЧНА ПОМИЛКА Selenium: {str(e)}")
        import traceback
        traceback.print_exc()
        driver_ready = False

# Решта коду залишається...
