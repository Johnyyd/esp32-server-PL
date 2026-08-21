import io
import edge_tts
from openai import AsyncOpenAI
from app.core.config import settings

groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=settings.GROQ_API_KEY,
)

async def transcribe_audio(audio_data: bytes) -> str:
    """Sử dụng Groq Whisper để STT."""
    try:
        from pydub import AudioSegment
        # Chuyển đổi mọi định dạng (webm/mp4/ogg) từ browser sang chuẩn WAV
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        clean_wav_bytes = wav_io.getvalue()

        # Gửi file dạng bytes
        file_obj = ("audio.wav", clean_wav_bytes, "audio/wav")
        response = await groq_client.audio.transcriptions.create(
            file=file_obj,
            model="whisper-large-v3",
            language="vi",
            temperature=0.0,
            prompt="Bật tắt thiết bị thông minh, bóng đèn, quạt, tivi, máy lạnh, thời tiết, thời sự. Bật PC giúp tôi đi. Thời sự hôm nay như thế nào?"
        )
        text = response.text.strip()
        
        # Lọc các câu rác (hallucination) thường gặp của Whisper do nhiễu im lặng
        hallucinations = [
            "hãy subscribe", "đăng ký kênh", "cảm ơn các bạn", "hẹn gặp lại",
            "chúc các bạn", "theo dõi kênh", "video tiếp theo", "xin chào các bạn",
            "cảm ơn quý vị", "đừng quên like", "nhà tài liệu", "tài liệu của tài liệu",
            "không có tài năng", "amara.org", "phụ đề được thực hiện"
        ]
        
        text_lower = text.lower().strip()
        
        # Nếu chỉ có độc mỗi chữ "tại sao?" hoặc "tại sao" mà không có context gì thêm
        if text_lower in ["tại sao?", "tại sao", "tại sao.", "tại sao!"]:
            print(f"[STT] Lọc bỏ câu nhiễu rác ngắn: {text}")
            return ""
        for h in hallucinations:
            if h in text_lower:
                print(f"[STT] Lọc bỏ câu nhiễu rác: {text}")
                return ""
                
        return text
    except Exception as e:
        print(f"Lỗi STT: {e}")
        return ""

async def synthesize_speech(text: str) -> bytes:
    """Sử dụng edge-tts để tạo âm thanh từ văn bản."""
    try:
        communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return b""
