import asyncio
import io
import time
from wyoming.server import AsyncServer, AsyncEventHandler
from wyoming.event import Event
from wyoming.info import Info, AsrProgram, AsrModel, TtsProgram, TtsVoice, Describe, Attribution, HandleProgram, HandleModel
from wyoming.audio import AudioChunk, AudioStop, AudioStart
from wyoming.asr import Transcribe, Transcript
from wyoming.tts import Synthesize
from wyoming.handle import Handled

# Import các logic xử lý AI sẵn có
from app.services.ai_service import process_text_intent_stream
from app.services.audio_service import transcribe_audio

# Cần thư viện pydub để lấy raw PCM cho Wyoming
from pydub import AudioSegment
import edge_tts

class WyomingAIHandler(AsyncEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_buffer = bytearray()
        self.is_stt = False

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            attr = Attribution(name="Trí Nguyễn", url="https://github.com/trinm2102")
            # Khai báo với Home Assistant rằng server này hỗ trợ STT, TTS, và cả Conversation
            info = Info(
                asr=[
                    AsrProgram(
                        name="groq-whisper",
                        description="Groq Whisper Siêu Tốc",
                        attribution=attr,
                        installed=True,
                        version="1.0",
                        models=[AsrModel(
                            name="whisper-large-v3", 
                            description="Whisper V3", 
                            attribution=attr,
                            installed=True,
                            version="1.0",
                            languages=["vi", "en"]
                        )]
                    )
                ],
                tts=[
                    TtsProgram(
                        name="edge-tts",
                        description="Edge TTS Siêu Tốc",
                        attribution=attr,
                        installed=True,
                        version="1.0",
                        voices=[TtsVoice(
                            name="vi-VN-HoaiMyNeural", 
                            description="Giọng Nữ Miền Nam", 
                            attribution=attr,
                            installed=True,
                            version="1.0",
                            languages=["vi"]
                        )]
                    )
                ],
                handle=[
                    HandleProgram(
                        name="llama3-conversation",
                        description="Llama 3 Siêu Tốc",
                        attribution=attr,
                        installed=True,
                        version="1.0",
                        models=[HandleModel(
                            name="llama3",
                            description="Llama 3",
                            attribution=attr,
                            installed=True,
                            version="1.0",
                            languages=["vi", "en"]
                        )]
                    )
                ]
            )
            await self.write_event(info.event())
            return True

        if Transcribe.is_type(event.type):
            self.is_stt = True
            self.audio_buffer.clear()
            return True

        if AudioChunk.is_type(event.type) and self.is_stt:
            chunk = AudioChunk.from_event(event)
            self.audio_buffer.extend(chunk.audio)
            return True

        if Transcript.is_type(event.type) and not self.is_stt:
            # HA đang dùng server này làm Conversation Agent (gửi text tới)
            transcript = Transcript.from_event(event)
            text = transcript.text
            print(f"[Wyoming] Conversation Agent nhận câu hỏi (từ Transcript): {text}", flush=True)
            asyncio.create_task(self.run_llm_conversation(text))
            return True

        if getattr(event, "type", "") == "recognize":
            # Một số phiên bản HA gửi event "recognize" cho Intent/Handle program
            text = event.data.get("text", "")
            print(f"[Wyoming] Conversation Agent nhận câu hỏi (từ Recognize): {text}", flush=True)
            asyncio.create_task(self.run_llm_conversation(text))
            return True

        if AudioStop.is_type(event.type) and self.is_stt:
            # Home Assistant đã gửi xong âm thanh (Người dùng ngừng nói)
            audio_bytes = bytes(self.audio_buffer)
            print(f"[Wyoming] Bắt đầu STT với đoạn âm thanh dài {len(audio_bytes)} bytes", flush=True)
            
            # Wyoming gửi raw PCM 16kHz 16-bit mono. Groq Whisper cần WAV.
            try:
                # Convert raw PCM to WAV in memory
                audio_segment = AudioSegment(
                    data=audio_bytes,
                    sample_width=2,
                    frame_rate=16000,
                    channels=1
                )
                wav_io = io.BytesIO()
                audio_segment.export(wav_io, format="wav")
                wav_bytes = wav_io.getvalue()
                
                text = await transcribe_audio(wav_bytes)
                print(f"[Wyoming] Kết quả STT: {text}", flush=True)
                
                if text:
                    await self.write_event(Transcript(text=text).event())
                else:
                    await self.write_event(Transcript(text="").event())
            except Exception as e:
                print(f"[Wyoming] Lỗi STT: {e}", flush=True)
                await self.write_event(Transcript(text="").event())
                
            self.is_stt = False
            return True

        if Synthesize.is_type(event.type):
            synth = Synthesize.from_event(event)
            user_text = synth.text
            print(f"[Wyoming] Nhận yêu cầu TTS với text: {user_text}", flush=True)
            
            if user_text.strip():
                try:
                    await self.write_event(
                        AudioStart(rate=16000, width=2, channels=1).event()
                    )
                    
                    # Chạy FFmpeg để convert MP3 stream sang raw PCM stream on the fly
                    # Tránh bị delay khi câu dài và sửa lỗi nhiễu tạp âm
                    process = await asyncio.create_subprocess_exec(
                        'ffmpeg', '-f', 'mp3', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', '-ar', '16000', 'pipe:1',
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL
                    )

                    async def write_to_ffmpeg():
                        try:
                            communicate = edge_tts.Communicate(user_text, "vi-VN-HoaiMyNeural")
                            async for chunk in communicate.stream():
                                if chunk["type"] == "audio":
                                    process.stdin.write(chunk["data"])
                                    await process.stdin.drain()
                        except Exception as e:
                            print(f"[Wyoming] Lỗi stream Edge-TTS: {e}")
                        finally:
                            process.stdin.close()
                    
                    async def read_from_ffmpeg():
                        chunk_size = 1024
                        buffer = bytearray()
                        while True:
                            data = await process.stdout.read(chunk_size)
                            if not data:
                                break
                            buffer.extend(data)
                            # Đảm bảo luôn gửi chính xác 1024 bytes (512 samples) mỗi lần
                            # để không làm hỏng byte-alignment của âm thanh PCM 16-bit
                            while len(buffer) >= chunk_size:
                                pcm_data = bytes(buffer[:chunk_size])
                                del buffer[:chunk_size]
                                await self.write_event(
                                    AudioChunk(rate=16000, width=2, channels=1, audio=pcm_data).event()
                                )
                                
                        # Gửi phần còn dư cuối cùng (nếu có)
                        if len(buffer) > 0:
                            remaining = bytes(buffer)
                            if len(remaining) % 2 != 0:
                                remaining = remaining[:-1] # Cắt byte lẻ cuối cùng để tránh lỗi alignment
                            if remaining:
                                await self.write_event(
                                    AudioChunk(rate=16000, width=2, channels=1, audio=remaining).event()
                                )

                    # Chạy song song: vừa tải MP3 về từ Microsoft, vừa decode ra PCM và đẩy thẳng lên ESP32
                    await asyncio.gather(write_to_ffmpeg(), read_from_ffmpeg())
                    await process.wait()
                        
                    await self.write_event(AudioStop().event())
                except Exception as e:
                    print(f"[Wyoming] Lỗi sinh TTS: {e}", flush=True)
                    
            return True

        return True

    async def run_llm_conversation(self, text: str):
        full_response = ""
        try:
            async for chunk in process_text_intent_stream(text):
                full_response += chunk
            print(f"[Wyoming] Llama 3 trả lời: {full_response}", flush=True)
            await self.write_event(Handled(text=full_response).event())
        except Exception as e:
            print(f"[Wyoming] Lỗi Llama 3: {e}", flush=True)
            await self.write_event(Handled(text="Xin lỗi, não tôi đang bị kẹt.").event())

async def start_wyoming_server(host="0.0.0.0", port=10400):
    print(f"Khởi động Wyoming Server tại {host}:{port}...", flush=True)
    server = AsyncServer.from_uri(f"tcp://{host}:{port}")
    await server.run(WyomingAIHandler)

if __name__ == "__main__":
    asyncio.run(start_wyoming_server())
