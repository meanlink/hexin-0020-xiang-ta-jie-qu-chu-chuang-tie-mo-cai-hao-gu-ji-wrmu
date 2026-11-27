from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.config import PROJECT_ID
from core.readiness import check_api

router = APIRouter(tags=["Runtime"])


@router.get("/health")
def health():
    try:
        check_api()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable", "project": PROJECT_ID})
    return {"status": "ok", "project": PROJECT_ID, "storage": "reachable", "redis": "reachable"}
