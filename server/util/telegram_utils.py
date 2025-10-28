import requests
from server.core.config import settings

def send_telegram_message(message):
    url = settings.TELEGRAM_BASE_API + "/sendMessage"
    resource = requests.post(url=url,
                            params={"chat_id": settings.TRACKED_CHAT_ID, "text": message, "parse_mode": "Markdown"})
    if resource.json().get("ok") is False:
        resource = requests.post(url=url,
                                 params={"chat_id": settings.TRACKED_CHAT_ID, "text": message})
    return resource.json()