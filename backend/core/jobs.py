from fastapi import APIRouter, Depends
from psycopg.types.json import Jsonb

from core.access import allow
from core.db import transaction
from core.errors import DomainError

router = APIRouter(tags=["Worker"])
JOB_FIELDS = "id, kind, status, result, error, created_at, completed_at"


def enqueue(conn, kind: str, payload: dict) -> dict:
    return conn.execute(
        "INSERT INTO jobs (kind,payload) VALUES (%s,%s) RETURNING id, kind, status",
        (kind, Jsonb(payload)),
    ).fetchone()


@router.get("/jobs/{job_id}")
def detail(job_id: int, _user=Depends(allow())):
    with transaction() as conn:
        row = conn.execute(
            f"SELECT {JOB_FIELDS} FROM jobs WHERE id=%s", (job_id,)
        ).fetchone()
    if row is None:
        raise DomainError(404, "Job not found")
    return row
