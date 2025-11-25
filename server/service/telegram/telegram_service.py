import requests

from server.core.config import settings

RESPONSE_MSG_ERROR = 'Xin chào hiện tại tôi đang gặp một chút sự cố, phụ huynh vui lòng thử lại'

class TelegramService:
    def __init__(self):
        self.base_url = settings.TELEGRAM_BASE_API
        self.chat_id = settings.TRACKED_CHAT_ID

    def send_message(self, message: str):
        url = self.base_url + "/sendMessage"
        response = requests.post(url=url,
                                 params={
                                     "chat_id": self.chat_id,
                                     "text": message,
                                     "parse_mode": "Markdown"
                                 })
        if response.json().get("ok") is False:
            response = requests.post(url=url,
                                     params={
                                         "chat_id": self.chat_id,
                                         "text": message
                                     })
        return response.json()

    def send_error_message(self):
        self.send_message(RESPONSE_MSG_ERROR)

    def send_photo_message(self, image_bytes: bytes, caption: str):
        url = self.base_url + "/sendPhoto"
        files = {'photo': ('image.jpg', image_bytes)}
        data = {'chat_id': self.chat_id, 'caption': caption}

        response = requests.post(
            url,
            data=data,
            files=files
        )

    def send_video_message(self, video_bytes: bytes, caption: str):
        url = self.base_url + "/sendVideo"
        files = {'video': ('video.mp4', video_bytes)}
        data = {'chat_id': self.chat_id, 'caption': caption}

        response = requests.post(
            url,
            data=data,
            files=files
        )

# === export ===
telegram_service = TelegramService()