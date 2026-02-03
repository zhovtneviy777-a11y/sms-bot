#!/usr/bin/env python3
import sys
import os
import time

print("=" * 50)
print("🧪 ТЕСТ Selenium в контейнері")
print("=" * 50)

# 1. Перевірка Chrome
print("\n1. 🔍 Перевірка встановлення Chrome...")
chrome_path = "/usr/bin/google-chrome-stable"
if os.path.exists(chrome_path):
    print(f"   ✅ Chrome знайдено: {chrome_path}")
    result = os.popen(f"{chrome_path} --version").read().strip()
    print(f"   📊 Версія: {result}")
else:
    print(f"   ❌ Chrome не знайдено!")
    print(f"   Шукав за шляхом: {chrome_path}")
    sys.exit(1)

# 2. Перевірка ChromeDriver
print("\n2. 🔍 Перевірка ChromeDriver...")
chromedriver_path = "/usr/local/bin/chromedriver"
if os.path.exists(chromedriver_path):
    print(f"   ✅ ChromeDriver знайдено: {chromedriver_path}")
    result = os.popen(f"{chromedriver_path} --version").read().strip()
    print(f"   📊 Версія: {result}")
else:
    print(f"   ❌ ChromeDriver не знайдено!")
    sys.exit(1)

# 3. Перевірка Python залежностей
print("\n3. 🔍 Перевірка Python бібліотек...")
try:
    import selenium
    print(f"   ✅ Selenium встановлено: v{selenium.__version__}")
except ImportError:
    print("   ❌ Selenium не встановлено!")
    sys.exit(1)

# 4. Основний тест Selenium
print("\n4. 🚀 Запуск тесту Selenium...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    start_time = time.time()
    
    # Налаштування Chrome
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = chrome_path
    
    print("   ⏳ Запускаємо Chrome...")
    driver = webdriver.Chrome(options=options)
    load_time = time.time() - start_time
    print(f"   ✅ Chrome запущено за {load_time:.1f} секунд")
    
    # Тестова сторінка
    print("   ⏳ Відкриваємо тестову сторінку...")
    driver.get("https://httpbin.org/html")
    
    # Перевірка
    print(f"   📄 Заголовок: {driver.title}")
    print(f"   🔗 URL: {driver.current_url}")
    
    # Проста взаємодія
    print("   ⏳ Перевіряємо взаємодію...")
    body = driver.find_element_by_tag_name("body")
    print(f"   ✅ Знайдено body: {len(body.text[:100])} символів тексту")
    
    # Закриваємо
    driver.quit()
    print("   ✅ Chrome успішно закрито")
    
    total_time = time.time() - start_time
    print(f"\n🎉 УСПІХ! Весь тест пройдено за {total_time:.1f} секунд")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ ПОМИЛКА під час тесту:")
    print(f"   Тип: {type(e).__name__}")
    print(f"   Повідомлення: {str(e)}")
    
    import traceback
    print("\n🔍 Traceback:")
    traceback.print_exc()
    
    sys.exit(1)
