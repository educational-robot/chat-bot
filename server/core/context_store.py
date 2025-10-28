from server.core.config import settings
from server.core.constants import *
from server.util.redis_manager import *

GLOBAL_CHAT_HISTORY = [] if settings.HISTORY_MODE == HistoryMode.IN_MEMORY else get_chat_history()

def reset_history():
    global GLOBAL_CHAT_HISTORY
    GLOBAL_CHAT_HISTORY = []