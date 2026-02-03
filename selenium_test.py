import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

def test_selenium():
    print("🧪 Тестуємо Selenium...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("https://www.google.com")
        print(f"✅ Успішно! Заголовок: {driver.title}")
        print(f"✅ URL: {driver.current_url}")
        
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Помилка: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_selenium()
    sys.exit(0 if success else 1)
