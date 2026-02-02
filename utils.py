# utils.py
import logging
import re
import asyncio
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import chromedriver_autoinstaller

def setup_logging():
    """Налаштування логування"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )

def validate_phone_number(phone: str) -> bool:
    """Валідація номера телефону"""
    pattern = r'^\+380\d{9}$'
    return bool(re.match(pattern, phone))

def create_selenium_driver() -> Optional[webdriver.Chrome]:
    """Створення Selenium драйвера"""
    try:
        # Автоматичне встановлення ChromeDriver
        chromedriver_autoinstaller.install()
        
        # Налаштування опцій
        chrome_options = Options()
        
        # Основні опції
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Додаткові опції для обходу блокувань
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Вимкнення вебдрайвер флагу
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Створення драйвера
        driver = webdriver.Chrome(options=chrome_options)
        
        # Виконання скрипта для приховування автоматизації
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    except Exception as e:
        logging.error(f"Помилка створення драйвера: {e}")
        return None

async def submit_phone_to_site(site_config: dict, phone_number: str) -> bool:
    """Відправка номера телефону на сайт"""
    driver = None
    try:
        # Створюємо драйвер
        driver = create_selenium_driver()
        if not driver:
            return False
        
        # Відкриваємо сторінку
        driver.get(site_config["url"])
        
        # Чекаємо завантаження
        await asyncio.sleep(2)
        
        # Пошук поля для телефону
        phone_input = None
        for selector in site_config["phone_selectors"]:
            try:
                phone_input = WebDriverWait(driver, site_config["timeout"]).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if phone_input:
                    break
            except:
                continue
        
        if not phone_input:
            logging.error(f"Не знайдено поле для телефону на {site_config['url']}")
            return False
        
        # Введення номера
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Пошук кнопки відправки
        submit_button = None
        for selector in site_config["submit_selectors"]:
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                if submit_button and submit_button.is_displayed() and submit_button.is_enabled():
                    break
                else:
                    submit_button = None
            except:
                continue
        
        # Клік по кнопці або відправка форми
        if submit_button:
            submit_button.click()
        else:
            # Спробуємо відправити форму
            try:
                phone_input.submit()
            except:
                # Шукаємо будь-яку кнопку на сторінці
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        break
        
        # Чекаємо трохи
        await asyncio.sleep(3)
        
        # Перевіряємо успішність
        # Тут можна додати перевірку URL або елементів на сторінці
        
        return True
        
    except TimeoutException:
        logging.error(f"Таймаут на сайті {site_config['url']}")
        return False
    except NoSuchElementException:
        logging.error(f"Елемент не знайдено на {site_config['url']}")
        return False
    except WebDriverException as e:
        logging.error(f"Помилка WebDriver на {site_config['url']}: {e}")
        return False
    except Exception as e:
        logging.error(f"Загальна помилка на {site_config['url']}: {e}", exc_info=True)
        return False
    finally:
        if driver:
            driver.quit()
