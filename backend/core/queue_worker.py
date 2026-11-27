import logging
import signal
import threading
import time

from psycopg.types.json import Jsonb

from core.db import transaction
from core.errors import DomainError
from core.readiness import heartbeat
from domain.tasks import run

log = logging.getLogger(__name__)
stop = threading.Event()


def publish_heartbeat():
    while not stop.is_set():
        try:
            heartbeat()
        except Exception:
            log.exception("Cannot update heartbeat")
        stop.wait(3)


def perform_one() -> bool:
    with transaction() as conn:
        job = conn.execute(
            "SELECT id, kind, payload FROM jobs WHERE status='queued' "
            "ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED"
        ).fetchone()
        if job is None:
            return False

        try:
            with conn.transaction():
                result = Jsonb(run(conn, job["kind"], job["payload"]))
                conn.execute(
                    "UPDATE jobs SET status='succeeded', result=%s, completed_at=now() WHERE id=%s",
                    (result, job["id"]),
                )
        except DomainError as exc:
            conn.execute(
                "UPDATE jobs SET status='failed', error=%s, completed_at=now() WHERE id=%s",
                (exc.detail, job["id"]),
            )
        except Exception:
            log.exception("Job %s failed", job["id"])
            conn.execute(
                "UPDATE jobs SET status='failed', error='Internal calculation error', completed_at=now() WHERE id=%s",
                (job["id"],),
            )
        return True


def main():
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    logging.basicConfig(level=logging.INFO)
    with transaction() as conn:
        conn.execute("SELECT 1 FROM jobs LIMIT 1")
    threading.Thread(target=publish_heartbeat, daemon=True).start()
    while not stop.is_set():
        try:
            if not perform_one():
                stop.wait(0.25)
        except Exception:
            log.exception("Worker could not transact")
            time.sleep(1)


if __name__ == "__main__":
    main()
