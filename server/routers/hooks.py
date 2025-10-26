from typing import List, Any

from fastapi import APIRouter
from google.genai.types import Content
from fastapi import Request

from server.models.telegram import *
from server.util.parents import *
from server.core.config import settings

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
            generate(message, request.app.state.text_data)
            return {"success": True}

    return {"success": False}