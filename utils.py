# utils.py
import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver():
    """Створення Selenium драйвера"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Автоматичне встановлення ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        return driver
    except Exception as e:
        logger.error(f"Помилка створення драйвера: {e}")
        return None

async def submit_to_olx(phone_number):
    """Введення номера на OLX"""
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return False
        
        driver.get("https://www.olx.ua/uk/")
        
        # Шукаємо кнопку входу
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-cy='login-link']"))
        )
        login_btn.click()
        
        # Вводимо номер
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel']"))
        )
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Кнопка "Далі"
        next_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        next_btn.click()
        
        await asyncio.sleep(3)
        logger.info(f"✅ OLX: номер {phone_number} введено")
        return True
        
    except Exception as e:
        logger.error(f"❌ OLX помилка: {e}")
        return False
    finally:
        if driver:
            driver.quit()

async def submit_to_rozetka(phone_number):
    """Введення номера на Rozetka"""
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return False
        
        driver.get("https://rozetka.com.ua/")
        
        # Кнопка входу
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".header-actions__button--user"))
        )
        login_btn.click()
        
        # Поле для телефону
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel']"))
        )
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Кнопка "Увійти"
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button.auth-modal__submit")
        submit_btn.click()
        
        await asyncio.sleep(3)
        logger.info(f"✅ Rozetka: номер {phone_number} введено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rozetka помилка: {e}")
        return False
    finally:
        if driver:
            driver.quit()

async def submit_to_prom(phone_number):
    """Введення номера на Prom.ua"""
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return False
        
        driver.get("https://prom.ua/")
        
        # Кнопка входу
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-qaid='auth_link']"))
        )
        login_btn.click()
        
        # Введення номера
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='phone']"))
        )
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Кнопка "Продовжити"
        continue_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        continue_btn.click()
        
        await asyncio.sleep(3)
        logger.info(f"✅ Prom.ua: номер {phone_number} введено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Prom.ua помилка: {e}")
        return False
    finally:
        if driver:
            driver.quit()

async def submit_to_nova_poshta(phone_number):
    """Введення номера на Nova Poshta"""
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return False
        
        driver.get("https://novaposhta.ua/")
        
        # Кнопка "Особистий кабінет"
        cabinet_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".personal-office"))
        )
        cabinet_btn.click()
        
        # Поле для телефону
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel']"))
        )
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        await asyncio.sleep(3)
        logger.info(f"✅ Nova Poshta: номер {phone_number} введено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Nova Poshta помилка: {e}")
        return False
    finally:
        if driver:
            driver.quit()

async def submit_to_epicentr(phone_number):
    """Введення номера на Epicentr"""
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return False
        
        driver.get("https://epicentrk.ua/")
        
        # Кнопка входу
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__login"))
        )
        login_btn.click()
        
        # Поле для телефону
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel']"))
        )
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Кнопка "Увійти"
        submit_btn = driver.find_element(By.CSS_SELECTOR, ".auth-form__submit")
        submit_btn.click()
        
        await asyncio.sleep(3)
        logger.info(f"✅ Epicentr: номер {phone_number} введено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Epicentr помилка: {e}")
        return False
    finally:
        if driver:
            driver.quit()

async def process_all_sites(phone_number):
    """Обробка номера на всіх сайтах"""
    results = {
        "OLX.ua": await submit_to_olx(phone_number),
        "Rozetka.com.ua": await submit_to_rozetka(phone_number),
        "Prom.ua": await submit_to_prom(phone_number),
        "NovaPoshta": await submit_to_nova_poshta(phone_number),
        "EpicentrK.ua": await submit_to_epicentr(phone_number)
    }
    return results
