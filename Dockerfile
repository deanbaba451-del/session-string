# Hafif bir Python imajı kullanıyoruz
FROM python:3.9-slim

# Çalışma dizinini oluştur
WORKDIR /app

# Gerekli dosyaları kopyala
COPY requirements.txt .
COPY main.py .

# Bağımlılıkları yükle
RUN pip install --no-cache-dir -r requirements.txt

# Render'ın beklediği portu dışarı aç (8080 varsayılan)
EXPOSE 8080

# Botu çalıştır
CMD ["python", "main.py"]
