from typing import List

from fastapi import APIRouter
from google.genai.types import Content

from server.models.telegram import *
from server.util.parents import *
from server.core.config import settings

router = APIRouter(
    prefix="/hooks",
    tags=["Hooks"]
)

IN_MEMORY_HISTORY: List[Content] = []

@router.post("/message")
def notify_telegram_message(noti: TelegramUpdate):
    if noti.message.chat.id == settings.TRACKED_CHAT_ID:
        message = noti.message.text
        generate(message, IN_MEMORY_HISTORY)
        return True
    return False