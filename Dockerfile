FROM python:3.9-slim

# Çalışma dizinini oluştur
WORKDIR /app

# Gerekli sistem araçlarını kur (SQLite için gerekebilir)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm kodları kopyala
COPY . .

# Flask portunu dış dünyaya aç (Render için 5000 standarttır)
EXPOSE 5000

# Botu başlat
CMD ["python", "main.py"]
