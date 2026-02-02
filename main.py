# main.py - найпростіший тест
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Bot starting...")
    
    # Перевіряємо токен
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN not found!")
        return
    
    logger.info(f"✅ BOT_TOKEN found: {token[:10]}...")
    
    # Просто працюємо
    while True:
        logger.info("🤖 Bot is alive and running")
        time.sleep(60)  # Чекаємо 1 хвилину

if __name__ == "__main__":
    main()
