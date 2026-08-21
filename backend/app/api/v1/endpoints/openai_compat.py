from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import time
from app.services.ai_service import process_text_intent

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Endpoint tương thích chuẩn OpenAI. 
    Home Assistant có thể dùng endpoint này qua tích hợp 'OpenAI Conversation'.
    """
    # Lấy tin nhắn cuối cùng của user
    user_message = next((msg.content for msg in reversed(request.messages) if msg.role == "user"), "")
    
    # Xử lý qua AI service của chúng ta (OpenRouter/Groq + Function Calling)
    response_text = await process_text_intent(user_message)
    
    # Trả về format chuẩn OpenAI
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }
