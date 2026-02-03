# main.py - тимчасово без Selenium
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константи
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://sms-bot-production-4260.up.railway.app{WEBHOOK_PATH}"

# Ініціалізація
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== КОМАНДИ БОТА =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 <b>Бот запущено!</b>\n\n"
        "Наразі тестовый режим.\n"
        "Функція введення номерів скоро буде доступна."
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    await message.answer("✅ <b>Статус:</b> Бот працює\n🌐 <b>Режим:</b> Вебхук")

@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    await message.answer("🔄 Тест пройдено успішно!")

# ===== HEALTHCHECK =====
async def health_check(request):
    return web.Response(text="OK", status=200)

# ===== ЗАПУСК =====
async def on_startup(bot: Bot):
    """Дії при запуску"""
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}")
    
    me = await bot.get_me()
    logger.info(f"🤖 Bot: @{me.username}")

async def on_shutdown(bot: Bot):
    """Дії при вимкненні"""
    logger.info("🛑 Shutting down...")

def main():
    """Запуск додатку"""
    app = web.Application()
    
    # Додаємо healthcheck
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Налаштовуємо вебхук
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Підключаємо бота
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    # Запускаємо сервер
    logger.info("🚀 Starting server...")
    web.run_app(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080))
    )

if __name__ == "__main__":
    main()
