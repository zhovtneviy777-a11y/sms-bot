# main.py
import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ВЕБ-СЕРВЕР ДЛЯ HEALTHCHECK =====
async def healthcheck(request):
    """Ендпоінт для healthcheck Railway"""
    return web.Response(text="OK", status=200)

async def start_web_server():
    """Запуск веб-сервера на порті 8080"""
    app = web.Application()
    app.router.add_get('/', healthcheck)
    app.router.add_get('/health', healthcheck)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("🌐 Web server started on port 8080 for healthcheck")
    return runner

# ===== TELEGRAM БОТ =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ Бот працює! Всі системи в нормі.")

@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    await message.answer("🔄 Тестова команда працює!")

async def start_bot():
    """Запуск Telegram бота"""
    logger.info("🤖 Starting Telegram bot...")
    await dp.start_polling(bot)

async def main():
    """Основна функція"""
    # Запускаємо веб-сервер для healthcheck
    web_runner = await start_web_server()
    
    # Запускаємо бота
    bot_task = asyncio.create_task(start_bot())
    
    logger.info("🚀 Application started successfully!")
    logger.info("✅ Healthcheck available at http://0.0.0.0:8080/health")
    
    try:
        # Чекаємо поки бот працює
        await bot_task
    except asyncio.CancelledError:
        logger.info("🛑 Shutting down...")
    finally:
        # Зупиняємо веб-сервер
        await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Application stopped by user")
