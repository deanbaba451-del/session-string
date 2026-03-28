# Hafif ve hızlı bir python imajı kullanıyoruz
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Gerekli paket listesini kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını içeri aktar
COPY . .

# Flask için portu aç (Render genelde 10000 veya 5000 kullanır)
EXPOSE 5000

# Botu ve Flask'ı başlatan komut
CMD ["python", "main.py"]
