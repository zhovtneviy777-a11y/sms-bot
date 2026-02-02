# main.py
import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ВЕБ-СЕРВЕР ДЛЯ HEALTHCHECK =====
async def healthcheck(request):
    """Ендпоінт для healthcheck Railway"""
    return web.Response(text="OK", status=200)

async def start_web_server():
    """Запуск веб-сервера"""
    app = web.Application()
    app.router.add_get('/', healthcheck)
    app.router.add_get('/health', healthcheck)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("✅ Web server started on port 8080")
    return runner

# ===== TELEGRAM БОТ =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

# Ініціалізація бота з polling
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 <b>Бот працює!</b>\n\n"
        "Доступні команди:\n"
        "/phone - Ввести номер телефону\n"
        "/status - Статус бота\n"
        "/help - Допомога"
    )

@dp.message(Command("phone"))
async def cmd_phone(message: types.Message):
    await message.answer("📱 <b>Введіть номер телефону:</b>\nФормат: +380XXXXXXXXX")

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    await message.answer("✅ <b>Бот активний</b>\nВсі системи працюють нормально")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("ℹ️ <b>Допомога:</b>\nВведіть /phone для початку роботи")

async def delete_webhook():
    """Видаляємо активний вебхук"""
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete webhook: {e}")
        return False

async def start_bot():
    """Запуск Telegram бота"""
    logger.info("🚀 Starting Telegram bot...")
    
    # Спочатку видаляємо вебхук
    if not await delete_webhook():
        logger.warning("⚠️ Continuing without deleting webhook...")
    
    # Запускаємо polling
    await dp.start_polling(bot, skip_updates=True)

async def main():
    """Основна функція"""
    # Запускаємо веб-сервер
    web_runner = await start_web_server()
    
    # Запускаємо бота
    bot_task = asyncio.create_task(start_bot())
    
    logger.info("🎉 Application fully started!")
    logger.info("📡 Bot is ready to receive messages...")
    
    try:
        # Чекаємо поки бот працює
        await bot_task
    except asyncio.CancelledError:
        logger.info("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        # Зупиняємо веб-сервер
        await web_runner.cleanup()
        logger.info("👋 Application stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Stopped by user")
