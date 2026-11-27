from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from core import audit, auth_routes, errors, jobs, runtime_routes
from core.bootstrap import migrate
from core.config import PROJECT_ID, SEED_DEMO
from core.request_context import RequestContextMiddleware
from domain.routes import router
from scripts.seed_demo import demo


@asynccontextmanager
async def lifespan(_app):
    migrate()
    if SEED_DEMO:
        try:
            demo()
        except Exception:
            logging.getLogger(__name__).exception("Demo data could not be installed")
    yield


app = FastAPI(
    title=PROJECT_ID, version="1.0.0", lifespan=lifespan,
    docs_url=None, redoc_url=None,
)
app.add_middleware(audit.AuditMiddleware)
app.add_middleware(RequestContextMiddleware)
errors.install(app)
for api in (runtime_routes.router, auth_routes.router, jobs.router, audit.router, router):
    app.include_router(api)
