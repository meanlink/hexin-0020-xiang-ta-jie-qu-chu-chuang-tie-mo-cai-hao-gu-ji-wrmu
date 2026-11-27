import logging

from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from core.access import allow
from core.db import transaction

router = APIRouter(tags=["Audit"])
logger = logging.getLogger(__name__)


def record(request_id, actor, method, path, status):
    try:
        with transaction() as conn:
            conn.execute(
                "INSERT INTO audit_events(request_id, actor, method, path, status) VALUES (%s,%s,%s,%s,%s)",
                (request_id, actor, method, path, status),
            )
    except Exception:
        logger.exception("Unable to write audit event %s", request_id)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            route = request.scope.get("route")
            await run_in_threadpool(
                record, request.state.request_id, getattr(request.state, "actor", None),
                request.method, getattr(route, "path", "<unmatched>"), response.status_code,
            )
        return response


@router.get("/audit")
def recent_events(limit: int = Query(25, ge=1, le=100), _user=Depends(allow("admin"))):
    with transaction() as conn:
        return conn.execute(
            "SELECT request_id, actor, method, path, status, happened_at "
            "FROM audit_events ORDER BY id DESC LIMIT %s",
            (limit,),
        ).fetchall()
