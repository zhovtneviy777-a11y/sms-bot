# Додаємо цю команду до основного main.py
@dp.message(Command("selenium_test"))
async def cmd_selenium_test(message: types.Message):
    await message.answer("🧪 <b>Тестую Selenium...</b>")
    
    try:
        # Імпортуємо тест
        from selenium_test import test_selenium
        import asyncio
        
        # Виконуємо в окремому потоці
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor() as executor:
            success = await asyncio.get_event_loop().run_in_executor(
                executor, test_selenium
            )
        
        if success:
            await message.answer(
                "✅ <b>Selenium тест пройдено!</b>\n\n"
                "✅ Бібліотеки встановлено\n"
                "✅ Webdriver-manager працює\n"
                "⏳ Chrome буде встановлено наступним кроком"
            )
        else:
            await message.answer("❌ <b>Selenium тест не пройдено</b>\nПеревірте логи.")
            
    except ImportError:
        await message.answer(
            "❌ <b>Selenium не встановлено</b>\n\n"
            "Додайте до requirements.txt:\n"
            "<code>selenium==4.16.0</code>\n"
            "<code>webdriver-manager==4.0.1</code>"
        )
    except Exception as e:
        await message.answer(f"❌ <b>Помилка:</b> {str(e)}")
