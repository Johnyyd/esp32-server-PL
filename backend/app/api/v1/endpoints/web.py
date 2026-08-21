from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from app.services.ai_service import process_text_intent, process_text_intent_stream
from app.services.audio_service import synthesize_speech, transcribe_audio
from app.services.ha_service import play_audio_on_ha
import time
import os

router = APIRouter()

# Đảm bảo thư mục static tồn tại
os.makedirs("static", exist_ok=True)

from fastapi import WebSocket, WebSocketDisconnect

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 AI Assistant</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .chat-container { width: 100%; max-width: 500px; background: #1e1e1e; border-radius: 12px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        h2 { text-align: center; color: #4CAF50; margin-top: 0; }
        .chat-box { height: 400px; overflow-y: auto; background: #2a2a2a; border-radius: 8px; padding: 10px; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 10px; border-radius: 8px; max-width: 80%; line-height: 1.4; }
        .msg.user { align-self: flex-end; background: #4CAF50; color: white; }
        .msg.bot { align-self: flex-start; background: #3a3a3a; color: #e0e0e0; }
        .input-group { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 12px; border: none; border-radius: 8px; background: #2a2a2a; color: white; outline: none; }
        button { padding: 12px 15px; border: none; border-radius: 8px; background: #4CAF50; color: white; cursor: pointer; font-weight: bold; transition: background 0.3s; }
        button:hover { background: #45a049; }
        button:disabled { background: #555; cursor: not-allowed; }
        .mic-btn { background: #f44336; }
        .mic-btn:hover { background: #d32f2f; }
        .mic-btn.recording { animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Bảo Bối AI</h2>
        <div class="chat-box" id="chatBox">
            <div class="msg bot">Xin chào! Mình là Bảo Bối. Bạn muốn yêu cầu mình làm gì nào?</div>
        </div>
        <div class="input-group">
            <button id="micBtn" class="mic-btn" onclick="toggleRecord()">🎤</button>
            <input type="text" id="textInput" placeholder="Nhập câu lệnh..." onkeypress="if(event.key === 'Enter') submitText()">
            <button id="sendBtn" onclick="submitText()">Gửi</button>
        </div>
    </div>
    <script>
        let ws;
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let currentBotMsgDiv = null;
        let typingQueue = "";
        let isTyping = false;

        function typeText() {
            if (typingQueue.length > 0 && currentBotMsgDiv) {
                isTyping = true;
                let char = typingQueue.charAt(0);
                typingQueue = typingQueue.substring(1);
                
                if (char === '\\n') {
                    currentBotMsgDiv.innerHTML += '<br>';
                } else {
                    currentBotMsgDiv.innerHTML += char;
                }
                
                document.getElementById('chatBox').scrollTop = document.getElementById('chatBox').scrollHeight;
                setTimeout(typeText, 15); // Tốc độ gõ 15ms/ký tự
            } else {
                isTyping = false;
            }
        }

        function connect() {
            const protocol = window.location.protocol === "https:" ? "wss" : "ws";
            ws = new WebSocket(`${protocol}://${window.location.host}/ws/chat`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'start') {
                    currentBotMsgDiv = document.createElement('div');
                    currentBotMsgDiv.className = 'msg bot';
                    document.getElementById('chatBox').appendChild(currentBotMsgDiv);
                    typingQueue = "";
                } else if (data.type === 'chunk') {
                    if (currentBotMsgDiv) {
                        typingQueue += data.content;
                        if (!isTyping) typeText();
                    }
                } else if (data.type === 'end') {
                    document.getElementById('sendBtn').disabled = false;
                    document.getElementById('sendBtn').innerText = 'Gửi';
                } else if (data.type === 'transcription') {
                    appendMsg(data.content, 'user');
                }
            };
            
            ws.onclose = function(e) {
                console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
                setTimeout(function() {
                    connect();
                }, 1000);
            };
        }
        
        connect();

        async function submitText() {
            const input = document.getElementById('textInput');
            const text = input.value.trim();
            if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
            
            appendMsg(text, 'user');
            input.value = '';
            
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('sendBtn').innerText = '...';
            
            ws.send(JSON.stringify({type: 'text', content: text}));
        }
        
        function appendMsg(text, sender) {
            const box = document.getElementById('chatBox');
            const div = document.createElement('div');
            div.className = 'msg ' + sender;
            div.innerText = text;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        async function toggleRecord() {
            const btn = document.getElementById('micBtn');
            if (isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                btn.classList.remove('recording');
                return;
            }
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = e => {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    audioChunks = [];
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        document.getElementById('sendBtn').disabled = true;
                        document.getElementById('sendBtn').innerText = '...';
                        ws.send(audioBlob); // Gửi binary frame
                        ws.send(JSON.stringify({type: 'listen_stop'})); // Báo server đã gửi xong audio
                    }
                };
                
                mediaRecorder.start(500); // Gửi chunk mỗi 500ms nếu muốn stream, hoặc gom lại

                isRecording = true;
                btn.classList.add('recording');
            } catch (err) {
                alert('Không thể truy cập Micro: ' + err);
            }
        }
    </script>
</body>
</html>
"""

@router.get("/")
async def get_web_ui():
    return HTMLResponse(content=HTML_CONTENT)

class WebSubmitRequest(BaseModel):
    text: str

@router.post("/submit")
async def handle_web_submit(request: Request, body: WebSubmitRequest):
    # 1. Gọi AI xử lý text
    reply_text = await process_text_intent(body.text)
    
    # 2. Tạo âm thanh TTS bằng edge-tts
    audio_bytes = await synthesize_speech(reply_text)
    
    if audio_bytes:
        import io
        from pydub import AudioSegment
        
        try:
            # Lưu thành file wav tạm thời
            filename = f"answer_{int(time.time())}.wav"
            filepath = os.path.join("static", filename)
            
            # Convert MP3 bytes to WAV using pydub
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            audio_segment.export(filepath, format="wav")
            
            # Lấy địa chỉ base URL của request hiện tại
            base_url = str(request.base_url).rstrip('/')
            media_url = f"{base_url}/static/{filename}"
            print(f"Đã tạo audio URL: {media_url}")
            
            # 3. Yêu cầu HA phát file mp3 này
            result = await play_audio_on_ha(media_url, "media_player.phong_ngu_esp32_s3_loa_esp32")
            print(f"Kết quả gọi HA: {result}")
        except Exception as e:
            import traceback
            print(f"Lỗi chuyển đổi/lưu audio: {e}\n{traceback.format_exc()}")
        
    return JSONResponse(content={"reply": reply_text})

import json
import asyncio
import edge_tts

def extract_sentence(text):
    for i, char in enumerate(text):
        if char in ['.', '?', '!', '\n']:
            if char == '\n' or (i + 1 < len(text) and text[i+1] == ' '):
                end_idx = i + 1 if char == '\n' else i + 2
                return text[:end_idx], text[end_idx:]
    return None, text

async def tts_streaming_worker(tts_queue: asyncio.Queue, websocket: WebSocket):
    """Worker nhận từng câu văn, dịch ra MP3 và stream trực tiếp qua WebSocket (Kiến trúc Xiaozhi)"""
    while True:
        sentence = await tts_queue.get()
        if sentence is None: # EOF
            tts_queue.task_done()
            break
            
        sentence = sentence.strip()
        if sentence:
            try:
                # Stream TTS audio back via WebSocket directly
                communicate = edge_tts.Communicate(sentence, "vi-VN-HoaiMyNeural")
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        # Gửi chunk MP3 thẳng qua WebSocket dưới dạng Binary Frame
                        await websocket.send_bytes(chunk["data"])
            except Exception as e:
                print(f"Lỗi TTS Streaming Worker: {e}")
                
        tts_queue.task_done()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    audio_buffer = bytearray()
    
    try:
        while True:
            # Nhận tin nhắn (Text hoặc Binary)
            message = await websocket.receive()
            
            if message.get("bytes") is not None:
                # Nhận luồng âm thanh liên tục (Xiaozhi Architecture)
                audio_buffer.extend(message["bytes"])
                # Trong thực tế, ESP32 sẽ gửi liên tục các chunk vài KB
            
            elif message.get("text") is not None:
                data = json.loads(message["text"])
                msg_type = data.get("type")
                
                text_intent = ""
                
                # Nếu nhận lệnh gửi Text thông thường, hoặc có lệnh ngắt luồng Audio (listen_stop)
                if msg_type == "listen_stop" or data.get("content"):
                    if audio_buffer:
                        # Đã nhận đủ âm thanh, bắt đầu giải mã STT
                        audio_bytes = bytes(audio_buffer)
                        audio_buffer.clear()
                        print(f"Bắt đầu STT với đoạn âm thanh dài {len(audio_bytes)} bytes", flush=True)
                        text_intent = await transcribe_audio(audio_bytes)
                        if text_intent:
                            await websocket.send_json({"type": "transcription", "content": text_intent})
                    else:
                        text_intent = data.get("content", "")
                        print(f"Nhận được Text trực tiếp: {text_intent}", flush=True)

                    if not text_intent:
                        await websocket.send_json({"type": "end"})
                        continue
                        
                    # Gửi type: start để UI tạo bong bóng chat
                    await websocket.send_json({"type": "start"})
                    
                    full_response = ""
                    async for chunk in process_text_intent_stream(text_intent):
                        await websocket.send_json({"type": "chunk", "content": chunk})
                        full_response += chunk
                        
                    await websocket.send_json({"type": "end"})
                    
                    # Phát âm thanh trên loa ESP32 qua Home Assistant
                    if full_response.strip():
                        audio_bytes = await synthesize_speech(full_response)
                        if audio_bytes:
                            import io, time, os
                            from pydub import AudioSegment
                            try:
                                filename = f"answer_{int(time.time())}.wav"
                                filepath = os.path.join("static", filename)
                                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
                                audio_segment.export(filepath, format="wav")
                                
                                # Yêu cầu HA phát file mp3 này
                                # Lấy IP của server (Giả sử host là ESP32 backend)
                                # Ta không lấy từ request.base_url được trong websocket dễ dàng
                                # Lấy từ biến môi trường hoặc IP tĩnh, tạm lấy IP máy chủ hiện tại
                                import socket
                                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                s.connect(("8.8.8.8", 80))
                                local_ip = s.getsockname()[0]
                                s.close()
                                
                                media_url = f"http://{local_ip}:6000/static/{filename}"
                                print(f"Đã tạo audio URL để phát trên ESP32: {media_url}")
                                
                                await play_audio_on_ha(media_url, "media_player.phong_ngu_esp32_s3_loa_esp32")
                            except Exception as e:
                                print(f"Lỗi phát loa ESP32 từ Web UI: {e}")
                    
    except WebSocketDisconnect:
        print("Web UI client ngắt kết nối WebSocket.")
    except Exception as e:
        import traceback
        print(f"Lỗi nghiêm trọng trong WebSocket: {e}\n{traceback.format_exc()}")

