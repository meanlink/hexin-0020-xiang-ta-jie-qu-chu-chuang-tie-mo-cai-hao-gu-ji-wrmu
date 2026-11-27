from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        if request.url.path.startswith("/auth/"):
            response.headers["Cache-Control"] = "no-store"
        return response
