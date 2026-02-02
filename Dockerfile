# Dockerfile
FROM python:3.11-slim

# 1. Встановлюємо Chrome (спрощений спосіб)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google.gpg \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 2. Встановлюємо ChromeDriver через webdriver-manager (буде встановлено при запуску)
# Тут лише встановлюємо необхідні залежності
RUN apt-get update && apt-get install -y unzip curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Копіюємо requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Копіюємо код
COPY . .

# 5. Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:8080/health', timeout=2); exit(0) if r.status_code == 200 else exit(1)" || exit 1

# 6. Запуск
CMD ["python", "main.py"]
