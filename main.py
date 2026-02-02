# main.py
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import config
from utils import (
    setup_logging,
    validate_phone_number,
    create_selenium_driver,
    submit_phone_to_site
)

# Налаштування логування
setup_logging()
logger = logging.getLogger(__name__)

# Ініціалізація бота
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Глобальні змінні для управління
active_tasks: Dict[int, List[asyncio.Task]] = {}
stop_flags: Dict[int, bool] = {}

# Стани для FSM
class BotStates(StatesGroup):
    waiting_for_phone = State()
    processing = State()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Ввести номер"), KeyboardButton(text="🛑 Зупинити")],
            [KeyboardButton(text="📊 Статус"), KeyboardButton(text="🌐 Сайти")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await message.answer(
        "👋 <b>Вітаю! Я бот для введення номерів телефонів на сайти.</b>\n\n"
        "📋 <b>Доступні команди:</b>\n"
        "/phone або кнопка '📱 Ввести номер' - Ввести номер телефону\n"
        "/stop або кнопка '🛑 Зупинити' - Зупинити всі процеси\n"
        "/status або кнопка '📊 Статус' - Перевірити статус\n"
        "/sites або кнопка '🌐 Сайти' - Показати доступні сайти\n"
        "/help - Допомога",
        reply_markup=keyboard
    )

# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
<b>📖 Довідка по боту:</b>

1. <b>Введення номера:</b>
   • Натисніть "📱 Ввести номер"
   • Введіть номер у форматі: <code>+380XXXXXXXXX</code>

2. <b>Доступні сайти:</b>
   • OLX.ua
   • Rozetka.com.ua
   • Prom.ua
   • NovaPoshta
   • EpicentrK.ua

3. <b>Керування:</b>
   • "🛑 Зупинити" - зупиняє всі активні процеси
   • "📊 Статус" - показує поточний статус

<b>⚠️ Увага:</b> Бот працює в тестовому режимі.
"""
    await message.answer(help_text)

# Команда /phone
@dp.message(Command("phone"))
@dp.message(F.text == "📱 Ввести номер")
async def cmd_phone(message: Message, state: FSMContext):
    await message.answer(
        "📱 <b>Будь ласка, введіть номер телефону:</b>\n"
        "<i>Формат: +380XXXXXXXXX</i>\n\n"
        "<i>Наприклад: +380991234567</i>"
    )
    await state.set_state(BotStates.waiting_for_phone)

# Обробка введення номера
@dp.message(BotStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone_number = message.text.strip()
    
    # Валідація номера
    if not validate_phone_number(phone_number):
        await message.answer(
            "❌ <b>Неправильний формат номеру!</b>\n\n"
            "Будь ласка, введіть номер у форматі:\n"
            "<code>+380XXXXXXXXX</code>\n\n"
            "<i>Наприклад: +380991234567</i>"
        )
        return
    
    await state.update_data(phone_number=phone_number)
    await state.set_state(BotStates.processing)
    
    # Запуск процесу
    await start_phone_submission(message.chat.id, phone_number)
    await message.answer(
        f"✅ <b>Номер {phone_number} прийнято!</b>\n\n"
        f"🔄 <i>Запускаю процес на {len(config.SITES_CONFIG)} сайтах...</i>"
    )

# Команда /stop
@dp.message(Command("stop"))
@dp.message(F.text == "🛑 Зупинити")
async def cmd_stop(message: Message):
    chat_id = message.chat.id
    
    if chat_id in stop_flags and not stop_flags[chat_id]:
        stop_flags[chat_id] = True
        await message.answer("⏳ <b>Зупиняю всі процеси...</b>")
        
        # Очистка завдань
        if chat_id in active_tasks:
            for task in active_tasks[chat_id]:
                if not task.done():
                    task.cancel()
            
            # Чекаємо завершення завдань
            try:
                await asyncio.gather(*active_tasks[chat_id], return_exceptions=True)
            except asyncio.CancelledError:
                pass
            
            del active_tasks[chat_id]
        
        await asyncio.sleep(1)
        await message.answer("✅ <b>Всі процеси зупинено!</b>")
        stop_flags[chat_id] = False
    else:
        await message.answer("ℹ️ <b>Немає активних процесів для зупинки</b>")

# Команда /status
@dp.message(Command("status"))
@dp.message(F.text == "📊 Статус")
async def cmd_status(message: Message):
    chat_id = message.chat.id
    now = datetime.now().strftime("%H:%M:%S")
    
    if chat_id in active_tasks and active_tasks[chat_id]:
        active_count = sum(1 for task in active_tasks[chat_id] if not task.done())
        await message.answer(
            f"📊 <b>Статус:</b> Активний\n"
            f"⏰ <b>Час:</b> {now}\n"
            f"🔄 <b>Активних завдань:</b> {active_count}\n"
            f"✅ <b>Завершено:</b> {len(active_tasks[chat_id]) - active_count}"
        )
    else:
        await message.answer(
            f"📊 <b>Статус:</b> Неактивний\n"
            f"⏰ <b>Час:</b> {now}\n"
            f"🔄 <b>Очікую на введення номера...</b>"
        )

# Команда /sites
@dp.message(Command("sites"))
@dp.message(F.text == "🌐 Сайти")
async def cmd_sites(message: Message):
    sites_list = "\n".join([f"• <b>{site}</b> - {data['url']}" 
                           for site, data in config.SITES_CONFIG.items()])
    
    await message.answer(
        f"🌐 <b>Доступні сайти:</b>\n\n"
        f"{sites_list}\n\n"
        f"<i>Всього: {len(config.SITES_CONFIG)} сайтів</i>"
    )

# Функція для запуску процесу
async def start_phone_submission(chat_id: int, phone_number: str):
    stop_flags[chat_id] = False
    active_tasks[chat_id] = []
    
    # Створюємо завдання для кожного сайту
    for site_name, config_data in config.SITES_CONFIG.items():
        if stop_flags.get(chat_id, False):
            break
            
        task = asyncio.create_task(
            process_site(chat_id, site_name, config_data, phone_number)
        )
        active_tasks[chat_id].append(task)

# Обробка одного сайту
async def process_site(chat_id: int, site_name: str, site_config: dict, phone_number: str):
    try:
        start_time = datetime.now()
        
        # Відправляємо повідомлення про початок
        await bot.send_message(
            chat_id,
            f"🚀 <b>Початок:</b> {site_name}\n"
            f"🕐 <i>Час початку:</i> {start_time.strftime('%H:%M:%S')}"
        )
        
        # Виконуємо введення номера
        success = await submit_phone_to_site(site_config, phone_number)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if success:
            await bot.send_message(
                chat_id,
                f"✅ <b>Успішно:</b> {site_name}\n"
                f"⏱️ <i>Час виконання:</i> {duration:.1f}с\n"
                f"🕐 <i>Час завершення:</i> {end_time.strftime('%H:%M:%S')}"
            )
        else:
            await bot.send_message(
                chat_id,
                f"⚠️ <b>Помилка:</b> {site_name}\n"
                f"⏱️ <i>Час виконання:</i> {duration:.1f}с\n"
                f"🕐 <i>Час завершення:</i> {end_time.strftime('%H:%M:%S')}"
            )
            
    except asyncio.CancelledError:
        await bot.send_message(chat_id, f"⏸️ <b>Скасовано:</b> {site_name}")
        raise
    except Exception as e:
        logger.error(f"Помилка для {site_name}: {e}", exc_info=True)
        await bot.send_message(
            chat_id,
            f"❌ <b>Критична помилка:</b> {site_name}\n"
            f"<i>Деталі:</i> {str(e)[:100]}..."
        )

# Обробка помилок
@dp.errors()
async def errors_handler(update, exception):
    logger.error(f"Update: {update}\nException: {exception}", exc_info=True)
    return True

# Запуск бота
async def main():
    logger.info("🚀 Запуск бота...")
    
    # Перевірка токена
    if not config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не встановлено!")
        sys.exit(1)
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("⏹️ Бот зупинено користувачем")
    except Exception as e:
        logger.error(f"❌ Помилка запуску: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
