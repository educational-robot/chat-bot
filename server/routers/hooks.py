from fastapi import APIRouter
from fastapi import Request

from server.core.config import settings
from server.models.telegram import *
from server.service.gemini.gemini_service import gemini_service

router = APIRouter(
    prefix="/hooks",
    tags=["Hooks"]
)

@router.post("/message", response_model=None)
async def notify_telegram_message(request: Request):
    body = await request.json()
    print('Received message:', body)

    if 'message' in body:
        noti = TelegramUpdate.model_validate(body)
        if noti.message.chat.id == settings.TRACKED_CHAT_ID:
            message = noti.message.text
            gemini_service.handle_user_message(message)
            return {"success": True}

    return {"success": False}