import redis, pickle

from server.core.config import settings

class RedisManager:
    def __init__(self):
        self.rd = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

    def put_chat_history(self, history):
        self.rd.set(settings.REDIS_HISTORY_KEY, pickle.dumps(history))

    def get_chat_history(self):
        data = self.rd.get(settings.REDIS_HISTORY_KEY)
        if data is None:
            return []
        return pickle.loads(self.rd.get(settings.REDIS_HISTORY_KEY))

# === export ===
redis_manager = RedisManager()