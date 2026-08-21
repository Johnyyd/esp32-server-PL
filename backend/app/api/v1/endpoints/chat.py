from fastapi import APIRouter
from app.api.v1.requests.chat_request import ChatRequest
from app.services.ai_service import process_text_intent

router = APIRouter()

@router.post("/text")
async def chat_text(request: ChatRequest):
    """API cho các thiết bị mạng local gửi lệnh dạng text."""
    response_text = await process_text_intent(request.text)
    return {"success": True, "data": {"response": response_text}, "error": None}
