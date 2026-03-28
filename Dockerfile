# Python 3.9 tabanlı hafif imaj
FROM python:3.9-slim

# Çalışma dizini
WORKDIR /app

# Gerekli dosyaları kopyala ve kütüphaneleri kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Flask portunu dışarı aç (Render için 5000)
EXPOSE 5000

# Botu ve Web Server'ı başlat
CMD ["python", "main.py"]
