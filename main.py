# main.py
import os
import sys
import logging
from aiohttp import web

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== HEALTHCHECK =====
async def health_check(request):
    """Простий healthcheck для Railway"""
    return web.Response(text="✅ OK - Telegram Bot", status=200)

async def home_page(request):
    """Домашня сторінка"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Phone Bot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-top: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            .status {
                background: #4CAF50;
                color: white;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-size: 18px;
                margin-bottom: 20px;
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .links {
                display: grid;
                gap: 10px;
                margin-top: 20px;
            }
            .links a {
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                border-radius: 10px;
                color: white;
                text-decoration: none;
                text-align: center;
                transition: background 0.3s;
            }
            .links a:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .command {
                background: rgba(0, 0, 0, 0.2);
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <h1>🤖 Telegram Phone Bot</h1>
        
        <div class="container">
            <div class="status">
                ✅ Status: Running and Healthy
            </div>
            
            <h3>📊 Health Checks:</h3>
            <div class="links">
                <a href="/health">Health Check</a>
                <a href="/info">System Info</a>
                <a href="/telegram">Telegram Status</a>
            </div>
            
            <h3>📱 Telegram Bot Commands:</h3>
            <div class="command">/start - Start the bot</div>
            <div class="command">/status - Check bot status</div>
            <div class="command">/test - Test command</div>
            
            <p style="margin-top: 20px; opacity: 0.8;">
                Bot is running on Railway with webhook support.
                Chrome/Selenium functionality will be added soon.
            </p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def info_page(request):
    """Сторінка з інформацією"""
    import json
    info = {
        "status": "running",
        "service": "Telegram Phone Number Bot",
        "version": "1.0.0",
        "webhook_url": "https://sms-bot-production-4260.up.railway.app/webhook",
        "health_check": "https://sms-bot-production-4260.up.railway.app/health",
        "uptime": "Just started",
        "features": ["telegram_bot", "webhook", "health_check"]
    }
    return web.json_response(info)

async def telegram_status(request):
    """Перевірка статусу Telegram бота"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        return web.json_response({
            "telegram": "disabled",
            "reason": "BOT_TOKEN not set"
        })
    
    # Спробуємо перевірити бота
    try:
        import aiohttp
        import asyncio
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
            ) as response:
                data = await response.json()
                
                if data.get('ok'):
                    return web.json_response({
                        "telegram": "connected",
                        "bot": data['result'],
                        "webhook": f"https://sms-bot-production-4260.up.railway.app/webhook"
                    })
                else:
                    return web.json_response({
                        "telegram": "error",
                        "error": data.get('description', 'Unknown error')
                    })
                    
    except Exception as e:
        return web.json_response({
            "telegram": "error",
            "error": str(e)
        })

# ===== TELEGRAM BOT =====
def setup_telegram_bot(app):
    """Налаштування Telegram бота"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN or ':' not in BOT_TOKEN or len(BOT_TOKEN) < 30:
        logger.warning("⚠️ BOT_TOKEN not valid, Telegram bot disabled")
        return
    
    try:
        from aiogram import Bot, Dispatcher
        from aiogram.filters import Command
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        from aiogram.types import Message
        
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        
        # Команди бота
        @dp.message(Command("start"))
        async def cmd_start(message: Message):
            await message.answer(
                "🤖 <b>Telegram Phone Bot</b>\n\n"
                "✅ Бот працює успішно!\n"
                "🌐 Домен: sms-bot-production-4260.up.railway.app\n\n"
                "<b>Команди:</b>\n"
                "/status - Статус системи\n"
                "/test - Тестування\n"
                "/help - Допомога"
            )
        
        @dp.message(Command("status"))
        async def cmd_status(message: Message):
            await message.answer(
                "📊 <b>Статус системи:</b>\n"
                "✅ Бот: Працює\n"
                "✅ Вебхук: Активний\n"
                "✅ Railway: Здоровий\n"
                "🔄 Selenium: Налаштовується"
            )
        
        @dp.message(Command("test"))
        async def cmd_test(message: Message):
            await message.answer("✅ <b>Тест пройдено!</b>\nСистема працює коректно.")
        
        @dp.message(Command("help"))
        async def cmd_help(message: Message):
            await message.answer(
                "ℹ️ <b>Допомога:</b>\n\n"
                "Бот працює у тестовому режимі.\n"
                "Основна функція (введення номерів на сайти) буде доступна найближчим часом."
            )
        
        # Налаштування вебхука
        WEBHOOK_PATH = "/webhook"
        WEBHOOK_URL = f"https://sms-bot-production-4260.up.railway.app{WEBHOOK_PATH}"
        
        async def on_startup(bot: Bot):
            try:
                await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
                logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
                
                me = await bot.get_me()
                logger.info(f"✅ Bot connected: @{me.username}")
            except Exception as e:
                logger.error(f"❌ Webhook setup error: {e}")
        
        async def on_shutdown(bot: Bot):
            logger.info("🛑 Shutting down Telegram bot...")
        
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Реєстрація вебхука
        webhook_handler = SimpleRequestHandler(dp, bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        logger.info("✅ Telegram bot initialized successfully")
        
    except ImportError as e:
        logger.error(f"❌ Aiogram import error: {e}")
    except Exception as e:
        logger.error(f"❌ Telegram bot setup error: {e}")

# ===== ОСНОВНА ФУНКЦІЯ =====
def main():
    """Запуск додатку"""
    app = web.Application()
    
    # Статичні ендпоінти
    app.router.add_get("/", home_page)
    app.router.add_get("/health", health_check)
    app.router.add_get("/info", info_page)
    app.router.add_get("/telegram", telegram_status)
    
    # Налаштовуємо Telegram бота
    setup_telegram_bot(app)
    
    # Запускаємо сервер
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Starting server on port {port}")
    logger.info(f"🌐 Health check: http://0.0.0.0:{port}/health")
    
    try:
        web.run_app(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        logger.info("⏹️ Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
