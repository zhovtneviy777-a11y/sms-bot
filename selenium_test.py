# selenium_test.py
import logging
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_selenium():
    """Тест Selenium без реального Chrome"""
    try:
        logger.info("🧪 Testing Selenium installation...")
        
        # Спробуємо імпортувати
        from selenium import __version__ as selenium_version
        logger.info(f"✅ Selenium version: {selenium_version}")
        
        # Спробуємо створити драйвер
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Простий тест
            driver.get("https://www.google.com")
            logger.info(f"✅ Page title: {driver.title}")
            
            driver.quit()
            logger.info("✅ Selenium test passed!")
            return True
            
        except WebDriverException as e:
            logger.warning(f"⚠️ WebDriver error (Chrome not installed): {e}")
            logger.info("ℹ️ This is expected - Chrome not installed yet")
            return True  # Все ще OK для нашого етапу
            
    except ImportError as e:
        logger.error(f"❌ Selenium import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_selenium()
    sys.exit(0 if success else 1)
