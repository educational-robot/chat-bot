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

def send_photo_message(image_bytes: bytes, caption: str):
    url = settings.TELEGRAM_BASE_API + "/sendPhoto"
    files = {'photo': ('image.jpg', image_bytes)}
    data = {'chat_id': settings.TRACKED_CHAT_ID, 'caption': caption}

    telegram_response = requests.post(
        url,
        data=data,
        files=files
    )

def send_video_message(video_bytes: bytes, caption: str):
    url = settings.TELEGRAM_BASE_API + "/sendVideo"
    files = {'video': ('video.mp4', video_bytes)}
    data = {'chat_id': settings.TRACKED_CHAT_ID, 'caption': caption}

    telegram_response = requests.post(
        url,
        data=data,
        files=files
    )