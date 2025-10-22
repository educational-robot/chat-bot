from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    TRACKED_CHAT_ID = int(os.getenv("TRACKED_CHAT_ID", 1))
    TELEGRAM_BASE_URL = os.getenv("TELEGRAM_BASE_URL", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    TELEGRAM_BASE_API = TELEGRAM_BASE_URL + BOT_TOKEN

    LMS_BASE_URL = os.getenv("LMS_BASE_URL", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

settings = Settings()