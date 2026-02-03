# main.py (оновлена функція process_phone)
@dp.message(PhoneState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    
    # Валідація номеру
    if phone.startswith('+380') and len(phone) == 13 and phone[1:].isdigit():
        await state.update_data(phone=phone)
        
        # Повідомляємо про початок
        await message.answer(
            f"✅ <b>Номер прийнято:</b> {phone}\n\n"
            f"🔄 <b>Починаю реальну обробку на 5 сайтах...</b>\n"
            f"Це займе 2-3 хвилини."
        )
        
        try:
            # Імпортуємо Selenium функції
            from utils import process_all_sites
            
            # Запускаємо обробку
            results = await process_all_sites(phone)
            
            # Формуємо звіт
            success_count = sum(1 for result in results.values() if result)
            
            report = "📊 <b>Звіт по обробці:</b>\n\n"
            for site, success in results.items():
                status = "✅ Успішно" if success else "❌ Не вдалось"
                report += f"{site}: {status}\n"
            
            report += f"\n<b>Результат:</b> {success_count}/5 сайтів оброблено"
            
            await message.answer(report)
            
            if success_count > 0:
                await message.answer(
                    f"🎉 <b>Обробка завершена!</b>\n\n"
                    f"<i>Якщо сайт підтримує SMS-підтвердження, "
                    f"перевірте телефон {phone} на наявність повідомлень.</i>"
                )
            else:
                await message.answer(
                    "⚠️ <b>Не вдалось обробити жоден сайт.</b>\n\n"
                    "<i>Можливі причини:</i>\n"
                    "1. Змінилась структура сайтів\n"
                    "2. Потрібна капча\n"
                    "3. Тимчасові технічні проблеми"
                )
                
        except ImportError:
            # Якщо Selenium не встановлено, симулюємо
            await message.answer(
                f"⚠️ <b>Selenium не встановлено</b>\n\n"
                f"Номер {phone} готовий до обробки.\n"
                f"Для реальної роботи потрібно встановити Selenium."
            )
            
        except Exception as e:
            await message.answer(f"❌ <b>Помилка обробки:</b>\n{str(e)}")
        
        await state.clear()
    else:
        await message.answer(
            "❌ <b>Неправильний формат!</b>\n\n"
            "Використовуйте: <code>+380XXXXXXXXX</code>\n"
            "Приклад: <code>+380991234567</code>\n\n"
            "Спробуйте ще раз: /phone"
        )
