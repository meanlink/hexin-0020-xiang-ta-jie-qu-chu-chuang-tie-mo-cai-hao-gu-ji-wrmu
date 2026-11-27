import redis

from core.config import REDIS_URL, WORKER_KEY
from core.db import transaction

cache = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)


def check_api():
    with transaction() as conn:
        conn.execute("SELECT 1 FROM users LIMIT 1")
    cache.ping()


def heartbeat():
    cache.set(WORKER_KEY, "ready", ex=20)


def check_worker():
    if not cache.exists(WORKER_KEY):
        raise RuntimeError("Worker heartbeat expired")


if __name__ == "__main__":
    check_worker()
