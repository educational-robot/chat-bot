import redis, pickle

from server.core.config import settings

rd = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

def put_chat_history(history):
    rd.set(settings.REDIS_HISTORY_KEY, pickle.dumps(history))

def get_chat_history():
    data = rd.get(settings.REDIS_HISTORY_KEY)
    if data is None:
        return []
    return pickle.loads(rd.get(settings.REDIS_HISTORY_KEY))