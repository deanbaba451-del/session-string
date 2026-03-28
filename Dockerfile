FROM python:3.10-slim-buster

# Sistem bağımlılıkları ve temizlik
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pip optimizasyonu
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Gunicorn ile çalıştırma (Render için en iyisi)
CMD ["python", "app.py"]
