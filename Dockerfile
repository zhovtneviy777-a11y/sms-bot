# Dockerfile
FROM python:3.11-slim

# 1. Встановлюємо Chrome (спрощено)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 2. ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver_linux64

# 3. Робоча директорія
WORKDIR /app

# 4. Python залежності
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 5. Копіюємо код
COPY . .

# 6. Запуск
CMD ["python", "main.py"]
