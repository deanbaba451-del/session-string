FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
# Render'ın portunu dışarı açıyoruz
EXPOSE 8080
CMD ["python", "main.py"]
