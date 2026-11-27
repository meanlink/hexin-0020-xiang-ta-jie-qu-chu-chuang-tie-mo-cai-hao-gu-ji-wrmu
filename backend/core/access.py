from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import JWT_SECRET, PROJECT_ID
from core.db import transaction
from core.errors import DomainError

bearer = HTTPBearer(auto_error=False)


def issue(user) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "iss": PROJECT_ID,
        "iat": now,
        "exp": now + timedelta(hours=2),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def identity(request: Request, auth: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if auth is None:
        raise DomainError(401, "Bearer token required")
    try:
        payload = jwt.decode(
            auth.credentials, JWT_SECRET, algorithms=["HS256"], issuer=PROJECT_ID,
            options={"require": ["sub", "iss", "iat", "exp"]},
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise DomainError(401, "Invalid or expired bearer token") from None
    with transaction() as conn:
        user = conn.execute(
            "SELECT id, username, role FROM users WHERE id = %s AND active",
            (user_id,),
        ).fetchone()
    if user is None:
        raise DomainError(401, "Account unavailable")
    request.state.actor = user["username"]
    return user


def allow(*roles: str):
    def permitted(user=Depends(identity)):
        if roles and user["role"] not in roles:
            raise DomainError(403, "Role is not permitted for this operation")
        return user

    return permitted
