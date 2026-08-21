# Sử dụng image Python 3.11 siêu nhẹ
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Khắc phục lỗi thiếu timezone hoặc các thư viện C nếu có (có thể bỏ qua nếu requirements thuần python)
RUN apt-get update && apt-get install -y gcc ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt dependencies trước (để tận dụng Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào thư mục làm việc
COPY . .

# Mở port 6000 (FastAPI) và 10500 (Wyoming)
EXPOSE 6000
EXPOSE 10500

# Khai báo đường dẫn python
ENV PYTHONPATH=/app

# Chạy FastAPI thông qua Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6000"]
