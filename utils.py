import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """Чекає на появу елемента"""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )

def safe_get(driver, url, max_retries=3):
    """Безпечне відкриття сторінки з повторами"""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            time.sleep(2)  # Чекаємо на завантаження
            return True
        except Exception as e:
            print(f"Спроба {attempt + 1} невдала: {str(e)}")
            time.sleep(2)
    return False
