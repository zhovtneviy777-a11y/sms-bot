# main.py - спрощений для запуску
import os
import sys
import logging
from aiohttp import web

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== HEALTHCHECK ЕНДПОІНТИ =====
async def health_check(request):
    return web.Response(text="✅ Telegram Bot is running", status=200)

async def home_page(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Phone Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .status { background: #4CAF50; color: white; padding: 10px; border-radius: 5px; }
            .container { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>🤖 Telegram Phone Bot</h1>
        <div class="status">✅ Status: Running</div>
        <div class="container">
            <h3>Health checks:</h3>
            <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/info">/info</a> - Bot info</li>
            </ul>
            <h3>Telegram Bot:</h3>
            <p>Bot is running with webhook. Use commands in Telegram:</p>
            <code>/start, /phone, /sites, /status, /help</code>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def info_page(request):
    import json
    info = {
        "status": "running",
        "service": "Telegram Phone Number Bot",
        "webhook": "https://sms-bot-production-4260.up.railway.app/webhook",
        "health": "https://sms-bot-production-4260.up.railway.app/health",
        "features": ["phone_number_processing", "multi_site_support"]
    }
    return web.json_response(info)

# ===== ЗАПУСК СЕРВЕРА =====
def main():
    """Простий веб-сервер для Railway"""
    app = web.Application()
    
    # Ендпоінти
    app.router.add_get("/", home_page)
    app.router.add_get("/health", health_check)
    app.router.add_get("/info", info_page)
    
    # Додаємо Telegram бота, якщо є токен
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if BOT_TOKEN and ':' in BOT_TOKEN and len(BOT_TOKEN) > 30:
        try:
            # Імпортуємо Telegram бота тільки якщо є токен
            from aiogram import Bot, Dispatcher
            from aiogram.filters import Command
            from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
            from aiogram.types import Message
            
            bot = Bot(token=BOT_TOKEN)
            dp = Dispatcher()
            
            # Прості команди без Selenium
            @dp.message(Command("start"))
            async def cmd_start(message: Message):
                await message.answer(
                    "🤖 <b>Телефонний бот</b>\n\n"
                    "Бот працює! Selenium функціонал налаштовується.\n\n"
                    "Команди:\n"
                    "/status - Статус\n"
                    "/test - Тест"
                )
            
            @dp.message(Command("status"))
            async def cmd_status(message: Message):
                await message.answer("✅ <b>Статус:</b> Бот працює\n🔄 <b>Selenium:</b> Налаштовується")
            
            @dp.message(Command("test"))
            async def cmd_test(message: Message):
                await message.answer("✅ <b>Тест пройдено!</b>\nБот відповідає коректно.")
            
            # Налаштування вебхука
            WEBHOOK_PATH = "/webhook"
            WEBHOOK_URL = f"https://sms-bot-production-4260.up.railway.app{WEBHOOK_PATH}"
            
            async def on_startup(bot: Bot):
                await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
                logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
                
                me = await bot.get_me()
                logger.info(f"✅ Bot: @{me.username}")
            
            async def on_shutdown(bot: Bot):
                logger.info("🛑 Shutting down...")
            
            dp.startup.register(on_startup)
            dp.shutdown.register(on_shutdown)
            
            # Реєструємо вебхук
            webhook_handler = SimpleRequestHandler(dp, bot)
            webhook_handler.register(app, path=WEBHOOK_PATH)
            setup_application(app, dp, bot=bot)
            
            logger.info("✅ Telegram bot initialized")
            
        except ImportError as e:
            logger.warning(f"⚠️ Aiogram not available: {e}")
        except Exception as e:
            logger.error(f"❌ Telegram bot error: {e}")
    else:
        logger.warning("⚠️ BOT_TOKEN not set, Telegram bot disabled")
    
    # Запускаємо сервер
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Starting server on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
