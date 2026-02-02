# main.py - проста тестова версія
import os
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Перевірка змінних
BOT_TOKEN = os.getenv("BOT_TOKEN")
logger.info(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}")

# Просто працюємо
if __name__ == "__main__":
    logger.info("🚀 Application started successfully!")
    print("✅ Bot is running!")
    # Тримаємо застосунок активним
    import time
    while True:
        time.sleep(10)
        logger.info("Still running...")
