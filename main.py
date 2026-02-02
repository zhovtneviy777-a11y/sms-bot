import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

load_dotenv()

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Стани для FSM
class PhoneState(StatesGroup):
    waiting_for_phone = State()
    active = State()

# Ініціалізація бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Глобальні змінні для управління
active_tasks = {}
stop_flags = {}

# Список сайтів з селекторами
SITES_CONFIG = {
    "OLX.ua": {
        "url": "https://www.olx.ua/",
        "phone_input_selector": "input[type='tel'], input[type='phone'], input[name*='phone'], input[id*='phone']",
        "method": "selenium"
    },
    "Rozetka.com.ua": {
        "url": "https://rozetka.com.ua/",
        "phone_input_selector": "input[type='tel'], input[type='phone']",
        "method": "selenium"
    },
    "Prom.ua": {
        "url": "https://prom.ua/",
        "phone_input_selector": "input[type='tel'], input[name*='phone']",
        "method": "selenium"
    },
    "NovaPoshta": {
        "url": "https://novaposhta.ua/",
        "phone_input_selector": "input[type='tel'], input[name*='phone']",
        "method": "selenium"
    },
    "EpicentrK.ua": {
        "url": "https://epicentrk.ua/",
        "phone_input_selector": "input[type='tel'], input[name*='phone']",
        "method": "selenium"
    }
}

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Вітаю! Я бот для введення номерів телефонів на сайти.\n\n"
        "📋 Доступні команди:\n"
        "/phone - Ввести номер телефону\n"
        "/stop - Зупинити всі процеси\n"
        "/status - Перевірити статус\n"
        "/sites - Показати доступні сайти"
    )

# Команда /phone
@dp.message(Command("phone"))
async def cmd_phone(message: Message, state: FSMContext):
    await message.answer("📱 Будь ласка, введіть номер телефону у форматі +380XXXXXXXXX:")
    await state.set_state(PhoneState.waiting_for_phone)

# Обробка введення номера
@dp.message(PhoneState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone_number = message.text.strip()
    
    # Валідація номера
    if not phone_number.startswith('+380') or len(phone_number) != 13 or not phone_number[1:].isdigit():
        await message.answer("❌ Неправильний формат номеру. Використовуйте +380XXXXXXXXX")
        return
    
    await state.update_data(phone_number=phone_number)
    await state.set_state(PhoneState.active)
    
    # Запуск процесу
    await start_phone_submission(message.chat.id, phone_number)
    await message.answer(f"✅ Номер {phone_number} прийнято. Запускаю процес...")

# Команда /stop
@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    chat_id = message.chat.id
    
    if chat_id in stop_flags:
        stop_flags[chat_id] = True
        await message.answer("🛑 Зупиняю всі процеси...")
        
        # Очистка
        if chat_id in active_tasks:
            for task in active_tasks[chat_id]:
                task.cancel()
            del active_tasks[chat_id]
            
        await asyncio.sleep(1)
        await message.answer("✅ Всі процеси зупинено")
    else:
        await message.answer("ℹ️ Немає активних процесів для зупинки")

# Команда /status
@dp.message(Command("status"))
async def cmd_status(message: Message):
    chat_id = message.chat.id
    if chat_id in active_tasks and active_tasks[chat_id]:
        await message.answer("🟢 Процеси активні")
    else:
        await message.answer("🔴 Процеси неактивні")

# Команда /sites
@dp.message(Command("sites"))
async def cmd_sites(message: Message):
    sites_list = "\n".join([f"• {site}" for site in SITES_CONFIG.keys()])
    await message.answer(f"🌐 Доступні сайти:\n\n{sites_list}")

# Функція для запуску процесу
async def start_phone_submission(chat_id, phone_number):
    stop_flags[chat_id] = False
    active_tasks[chat_id] = []
    
    # Запускаємо для кожного сайту
    for site_name, config in SITES_CONFIG.items():
        if stop_flags.get(chat_id, False):
            break
            
        task = asyncio.create_task(
            submit_to_site(chat_id, site_name, config, phone_number)
        )
        active_tasks[chat_id].append(task)

# Функція відправки на сайт
async def submit_to_site(chat_id, site_name, config, phone_number):
    try:
        await bot.send_message(chat_id, f"🔄 Початок роботи з {site_name}...")
        
        if config["method"] == "selenium":
            success = await run_selenium_submission(
                config["url"], 
                config["phone_input_selector"], 
                phone_number
            )
        else:
            success = False
        
        if success:
            await bot.send_message(chat_id, f"✅ {site_name}: номер успішно введено")
        else:
            await bot.send_message(chat_id, f"⚠️ {site_name}: не вдалося знайти поле або виникла помилка")
            
    except Exception as e:
        logger.error(f"Помилка для {site_name}: {e}")
        await bot.send_message(chat_id, f"❌ {site_name}: помилка - {str(e)}")

# Selenium функція
async def run_selenium_submission(url, selector, phone_number):
    driver = None
    try:
        # Налаштування для Railway (без GUI)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Для Railway потрібно вказати шлях до Chrome
        chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium-browser")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        driver.get(url)
        
        # Пошук поля для телефону
        wait = WebDriverWait(driver, 10)
        phone_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        
        # Введення номера
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Спроба відправки форми
        try:
            phone_input.submit()
        except:
            # Якщо не вдається відправити форму, шукаємо кнопку
            submit_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "button[type='submit'], input[type='submit'], .submit-btn, .login-btn")
            if submit_buttons:
                submit_buttons[0].click()
        
        await asyncio.sleep(3)  # Чекаємо завантаження
        return True
        
    except Exception as e:
        logger.error(f"Selenium помилка: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
