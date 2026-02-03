# main.py
import os
import sys
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ПЕРЕВІРКА ТОКЕНА =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Детальна перевірка токена
def validate_bot_token(token):
    """Перевірка формату токена Telegram бота"""
    if not token:
        logger.error("❌ BOT_TOKEN is empty!")
        return False
    
    if len(token) < 30:
        logger.error(f"❌ Token too short: {len(token)} chars")
        return False
    
    # Перевірка формату: числа:букви
    if ':' not in token:
        logger.error("❌ Token format invalid: no ':' found")
        return False
    
    parts = token.split(':')
    if len(parts) != 2:
        logger.error(f"❌ Token format invalid: {len(parts)} parts")
        return False
    
    if not parts[0].isdigit():
        logger.error(f"❌ First part not numeric: {parts[0]}")
        return False
    
    logger.info(f"✅ Token format valid (length: {len(token)})")
    return True

# Перевіряємо токен
if not BOT_TOKEN:
    logger.error("""
    ❌❌❌ BOT_TOKEN NOT FOUND! ❌❌❌
    
    Додайте BOT_TOKEN до Railway Variables:
    1. Відкрийте Railway Dashboard
    2. Виберіть проект
    3. Вкладка "Variables"
    4. Натисніть "+ New Variable"
    5. Name: BOT_TOKEN
    6. Value: ваш токен (отриманий від @BotFather)
    7. Description: Telegram Bot Token
    """)
    sys.exit(1)

if not validate_bot_token(BOT_TOKEN):
    logger.error(f"""
    ❌❌❌ INVALID BOT_TOKEN! ❌❌❌
    
    Ваш токен: {BOT_TOKEN[:10]}... (приховано)
    
    Правильний формат: 1234567890:AAHdGvP9bQwVcXzZYL8kKmNt8rQpLmNoJKl
    
    Як отримати токен:
    1. Відкрийте Telegram
    2. Знайдіть @BotFather
    3. Надішліть /newbot
    4. Дотримуйтесь інструкцій
    5. Скопіюйте токен (не діліться ним!)
    """)
    sys.exit(1)

# ===== ІМПОРТИ ПІСЛЯ ПЕРЕВІРКИ =====
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Ініціалізація бота (тепер без помилки)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== КОМАНДИ БОТА =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 <b>Бот запущено!</b>\n\n"
        "Токен перевірено успішно!\n"
        "Функції скоро будуть доступні."
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    await message.answer("✅ <b>Статус:</b> Бот працює\n🔑 <b>Токен:</b> Валідний")

# ===== HEALTHCHECK =====
async def health_check(request):
    return web.Response(text="OK - Bot is running", status=200)

async def token_check(request):
    """Ендпоінт для перевірки токена"""
    token_preview = f"{BOT_TOKEN[:10]}..." if BOT_TOKEN else "Not set"
    return web.Response(
        text=f"Token: {token_preview}\nValid: {validate_bot_token(BOT_TOKEN)}",
        status=200
    )

# ===== ЗАПУСК =====
async def on_startup(bot: Bot):
    logger.info("🚀 Bot starting up...")
    
    # Перевіряємо підключення
    try:
        me = await bot.get_me()
        logger.info(f"✅ Bot connected: @{me.username} ({me.first_name})")
        
        # Встановлюємо вебхук
        WEBHOOK_URL = f"https://sms-bot-production-4260.up.railway.app/webhook"
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        logger.info(f"✅ Webhook set: {WEBHOOK_URL}")
        
    except Exception as e:
        logger.error(f"❌ Bot connection failed: {e}")

async def on_shutdown(bot: Bot):
    logger.info("🛑 Shutting down...")

def main():
    app = web.Application()
    
    # Ендпоінти
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_get("/token", token_check)  # Для перевірки токена
    
    # Налаштовуємо бота
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    webhook_handler = SimpleRequestHandler(dp, bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Запускаємо
    logger.info("🌐 Starting web server...")
    web.run_app(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080))
    )

if __name__ == "__main__":
    main()
