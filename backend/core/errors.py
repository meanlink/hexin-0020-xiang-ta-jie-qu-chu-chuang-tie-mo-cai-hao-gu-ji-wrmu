from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg.errors import ForeignKeyViolation, UniqueViolation


class DomainError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


async def domain_error(_request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status, content={"detail": exc.detail})


async def write_conflict(_request: Request, exc: Exception):
    detail = "A referenced record changed" if isinstance(exc, ForeignKeyViolation) else "Record already exists"
    return JSONResponse(status_code=409, content={"detail": detail})


def install(app):
    app.add_exception_handler(DomainError, domain_error)
    app.add_exception_handler(ForeignKeyViolation, write_conflict)
    app.add_exception_handler(UniqueViolation, write_conflict)
