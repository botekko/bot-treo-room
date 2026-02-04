# Sử dụng Python 3.10
FROM python:3.10-slim

# Cài đặt FFmpeg VÀ thư viện Opus (Quan trọng cho Voice)
RUN apt-get update && \
    apt-get install -y ffmpeg libffi-dev libnacl-dev libopus-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code bot
COPY . .

# Chạy bot
CMD ["python", "bot.py"]
