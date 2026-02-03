# Dockerfile
FROM python:3.11-slim

# 1. Базові залежності
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Python залежності
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Копіюємо код
COPY . .

CMD ["python", "main.py"]
