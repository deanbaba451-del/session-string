FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Sadece gereksinimleri kuruyoruz
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
