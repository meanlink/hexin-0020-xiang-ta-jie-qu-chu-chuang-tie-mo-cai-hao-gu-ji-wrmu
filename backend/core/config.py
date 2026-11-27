import os


def required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


DATABASE_URL = required("DATABASE_URL")
REDIS_URL = required("REDIS_URL")
PROJECT_ID = required("PROJECT_ID")
JWT_SECRET = required("JWT_SECRET")
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET requires at least 32 characters")
SEED_DEMO = os.environ.get("SEED_DEMO", "").lower() == "true"
WORKER_KEY = f"{PROJECT_ID}:worker:heartbeat"
