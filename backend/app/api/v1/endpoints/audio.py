from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.audio_service import transcribe_audio, synthesize_speech
from app.services.ai_service import process_text_intent

router = APIRouter()

@router.websocket("/stream")
async def audio_stream(websocket: WebSocket):
    """WebSocket cho ESP32-S3 gửi audio và nhận lại audio."""
    await websocket.accept()
    try:
        while True:
            # Nhận audio chunk từ ESP32-S3
            audio_data = await websocket.receive_bytes()
            
            # STT
            text = await transcribe_audio(audio_data)
            if not text:
                continue
                
            print(f"User said: {text}")
            
            # LLM
            response_text = await process_text_intent(text)
            print(f"AI response: {response_text}")
            
            # TTS
            audio_response = await synthesize_speech(response_text)
            
            # Trả audio về ESP32-S3
            await websocket.send_bytes(audio_response)
            
    except WebSocketDisconnect:
        print("ESP32-S3 ngắt kết nối WebSocket.")
