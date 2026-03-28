# Daha güncel ve desteklenen bir baz imaj kullanıyoruz
FROM python:3.10-slim-bookworm

# Sistem bağımlılıklarını kuruyoruz (Bookworm ile depolar sorunsuz çalışır)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pip ve bağımlılık kurulumu
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Uygulamayı başlat
CMD ["python", "app.py"]
