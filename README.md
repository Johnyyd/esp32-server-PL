# ESP32-S3 AI Backend

Một backend đa chức năng được thiết kế để hoạt động cùng với phần cứng ESP32-S3, hỗ trợ tích hợp trí tuệ nhân tạo (LLMs), xử lý âm thanh (TTS/STT), và liên kết với Home Assistant thông qua giao thức Wyoming.

## 🚀 Tính năng nổi bật
- **FastAPI Server**: Cung cấp các API RESTful tốc độ cao để quản lý Chat, Audio, Web UI.
- **Tích hợp LLM**: Hỗ trợ nền tảng OpenRouter, Groq và tương thích với API của OpenAI.
- **Xử lý âm thanh**: Tích hợp Edge TTS, Pydub và FFMPEG để chuyển đổi văn bản thành giọng nói tiếng Việt/Anh và xử lý file audio.
- **Tích hợp Home Assistant (HA)**: 
  - Gọi API HA để điều khiển các thiết bị nhà thông minh (Smart Home).
  - **Wyoming Server (Port 10500)**: Tích hợp trực tiếp với tính năng Voice Assistant của Home Assistant.
- **Tìm kiếm trên Internet**: Sử dụng DuckDuckGo Search (ddgs) để cung cấp thông tin liên tục, thời gian thực cho AI.
- **Dockerized**: Triển khai dễ dàng bằng Docker.

## 🛠 Yêu cầu hệ thống
- Python 3.11+
- [FFmpeg](https://ffmpeg.org/download.html) (Bắt buộc cài đặt trên máy hoặc sử dụng Docker để Pydub xử lý âm thanh)
- Docker (Nếu bạn muốn chạy qua container)

## ⚙️ Cài đặt & Khởi chạy (Local)

1. **Clone repository:**
   ```bash
   git clone <repo-url>
   cd esp32-server-PL/backend
   ```

2. **Cài đặt môi trường ảo và các thư viện:**
   ```bash
   python -m venv venv
   # Kích hoạt môi trường ảo:
   # Trên Windows:
   venv\Scripts\activate
   # Trên macOS/Linux:
   source venv/bin/activate  

   pip install -r requirements.txt
   ```

3. **Cấu hình môi trường (.env):**
   Tạo file `.env` trong thư mục `backend/` dựa trên cấu trúc sau:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=openai/gpt-oss-120b
   ESP32_IP=192.168.100.x
   HA_URL=http://192.168.100.x:8123
   HA_TOKEN=your_home_assistant_long_lived_access_token
   ```

4. **Khởi chạy Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 6000
   ```
   *FastAPI server sẽ chạy ở port `6000`, và Wyoming Server sẽ tự động được chạy ngầm ở port `10500`.*

## 🐳 Triển khai bằng Docker

1. **Build image:**
   ```bash
   cd backend
   docker build -t esp32-ai-backend .
   ```

2. **Chạy container:**
   ```bash
   docker run -d \
     --name esp32_backend \
     -p 6000:6000 \
     -p 10500:10500 \
     --env-file .env \
     esp32-ai-backend
   ```

## 📚 API Endpoints chính
- `/api/v1/chat`: Xử lý giao tiếp với LLM.
- `/api/v1/audio`: Các API liên quan đến âm thanh và chuyển đổi Text-to-Speech.
- `/api/v1/openai`: Lớp API tương thích với cấu trúc của OpenAI để dễ dàng kết nối với các ứng dụng bên thứ 3.
- `/`: Giao diện Web UI để quản lý hệ thống.

## 🤝 Tích hợp Home Assistant
Ứng dụng này có thể hoạt động như một Wyoming Satellite cho HA. Bằng cách thêm Integration **Wyoming Protocol** vào Home Assistant và trỏ tới địa chỉ IP của server (kèm port `10500`), bạn có thể sử dụng các luồng xử lý giọng nói tuỳ chỉnh cho hệ thống nhà thông minh của mình.
