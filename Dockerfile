# Dockerfile
FROM python:3.11-slim

# 1. Оновлюємо систему та встановлюємо базові залежності
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Python залежності (без Selenium спочатку)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Копіюємо код
COPY . .

CMD ["python", "main.py"]
