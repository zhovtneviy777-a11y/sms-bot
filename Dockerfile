# Dockerfile
FROM python:3.11-slim

# 1. Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 2. Встановлюємо ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip

# 3. Робоча директорія
WORKDIR /app

# 4. Копіюємо requirements та встановлюємо ПОСТУПОВО
COPY requirements.txt .

# Спершу встановлюємо pip та базові залежності
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Потім встановлюємо залежності по одній
RUN pip install --no-cache-dir aiogram==3.5.0 && \
    pip install --no-cache-dir aiohttp==3.8.6 && \
    pip install --no-cache-dir selenium==4.15.2 && \
    pip install --no-cache-dir python-dotenv==1.0.0

# 5. Копіюємо код
COPY . .

# 6. Запускаємо бота
CMD ["python", "main.py"]
