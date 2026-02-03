# main.py
import os
import sys
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ПЕРЕВІРКА ТОКЕНА =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or ':' not in BOT_TOKEN or len(BOT_TOKEN) < 30:
    logger.error("❌ Invalid BOT_TOKEN!")
    sys.exit(1)

# ===== СТАНИ БОТА =====
class PhoneState(StatesGroup):
    waiting_for_phone = State()

# ===== ІНІЦІАЛІЗАЦІЯ =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== КОМАНДИ БОТА =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 <b>Телефонний бот</b>\n\n"
        "Доступні команди:\n"
        "/phone - Ввести номер телефону\n"
        "/sites - Список сайтів\n"
        "/status - Статус бота\n"
        "/help - Допомога\n"
        "/test - Тестування"
    )

@dp.message(Command("phone"))
async def cmd_phone(message: types.Message, state: FSMContext):
    await message.answer(
        "📱 <b>Введіть номер телефону:</b>\n\n"
        "<i>Формат: +380XXXXXXXXX</i>\n"
        "<i>Наприклад: +380991234567</i>"
    )
    await state.set_state(PhoneState.waiting_for_phone)

@dp.message(PhoneState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    
    # Валідація номеру
    if phone.startswith('+380') and len(phone) == 13 and phone[1:].isdigit():
        await state.update_data(phone=phone)
        
        await message.answer(
            f"✅ <b>Номер прийнято:</b> {phone}\n\n"
            f"🔄 <b>Починаю обробку на 5 сайтах:</b>\n"
            f"• OLX.ua\n"
            f"• Rozetka.com.ua\n"
            f"• Prom.ua\n"
            f"• NovaPoshta\n"
            f"• EpicentrK.ua\n\n"
            f"<i>Це тестовий режим. Selenium функціонал буде додано найближчим часом.</i>"
        )
        
        # Симуляція обробки
        import asyncio
        sites = ["OLX.ua", "Rozetka.com.ua", "Prom.ua", "NovaPoshta", "EpicentrK.ua"]
        
        for site in sites:
            await asyncio.sleep(1)  # Симуляція затримки
            await message.answer(f"🌐 <b>{site}:</b> Номер успішно введено")
        
        await message.answer("🎉 <b>Обробка завершена!</b>\nУсі 5 сайтів оброблено успішно.")
        
        await state.clear()
    else:
        await message.answer(
            "❌ <b>Неправильний формат!</b>\n\n"
            "Використовуйте: <code>+380XXXXXXXXX</code>\n"
            "Приклад: <code>+380991234567</code>\n\n"
            "Спробуйте ще раз: /phone"
        )

@dp.message(Command("sites"))
async def cmd_sites(message: types.Message):
    sites = [
        "• OLX.ua",
        "• Rozetka.com.ua", 
        "• Prom.ua",
        "• NovaPoshta",
        "• EpicentrK.ua"
    ]
    
    await message.answer(
        "🌐 <b>Доступні сайти:</b>\n\n" +
        "\n".join(sites) +
        "\n\n<i>Всього: 5 сайтів</i>"
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    await message.answer(
        "📊 <b>Статус бота:</b>\n"
        "✅ Бот працює\n"
        "🌐 Режим: Вебхук\n"
        "📱 Функції: Активні\n"
        "⚡ Selenium: Скоро буде\n"
        "🔗 Домен: sms-bot-production-4260.up.railway.app"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "ℹ️ <b>Допомога:</b>\n\n"
        "1. Натисніть /phone\n"
        "2. Введіть номер: +380XXXXXXXXX\n"
        "3. Бот обробить запит на 5 сайтах\n"
        "4. Отримайте звіт\n\n"
        "<i>Наразі в тестовому режимі</i>"
    )

@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    await message.answer("✅ <b>Тест пройдено!</b>\nБот працює коректно.")

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    await message.answer("🛑 <b>Команда стоп:</b>\nУ реальному режимі зупинить всі процеси.")

# ===== ВЕБ ЕНДПОІНТИ =====
async def health_check(request):
    return web.Response(text="✅ Telegram Phone Bot is running", status=200)

async def webhook_info(request):
    """Інформація про вебхук"""
    info = {
        "status": "running",
        "webhook": "https://sms-bot-production-4260.up.railway.app/webhook",
        "health": "https://sms-bot-production-4260.up.railway.app/health",
        "bot": "Telegram Phone Number Bot"
    }
    return web.json_response(info)

# ===== ЗАПУСК БОТА =====
async def on_startup(bot: Bot):
    """Дії при запуску"""
    # Встановлюємо вебхук
    WEBHOOK_URL = "https://sms-bot-production-4260.up.railway.app/webhook"
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    
    # Інформація про бота
    me = await bot.get_me()
    logger.info(f"✅ Bot started: @{me.username}")
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
    
    # Виводимо команди для користувача
    logger.info("\n" + "="*50)
    logger.info("🤖 Бот запущено успішно!")
    logger.info(f"🌐 Вебхук: {WEBHOOK_URL}")
    logger.info(f"👤 Бот: @{me.username}")
    logger.info("📋 Доступні команди в Telegram:")
    logger.info("  /start - Початок роботи")
    logger.info("  /phone - Ввести номер телефону")
    logger.info("  /sites - Список сайтів")
    logger.info("  /status - Статус бота")
    logger.info("  /help - Допомога")
    logger.info("="*50)

async def on_shutdown(bot: Bot):
    """Дії при зупинці"""
    logger.info("🛑 Bot shutting down...")

def main():
    """Запуск програми"""
    app = web.Application()
    
    # Веб ендпоінти
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_get("/info", webhook_info)
    
    # Налаштовуємо бота
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Вебхук
    webhook_handler = SimpleRequestHandler(dp, bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Запускаємо
    logger.info("🚀 Starting Telegram Phone Bot...")
    web.run_app(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080))
    )

if __name__ == "__main__":
    main()
