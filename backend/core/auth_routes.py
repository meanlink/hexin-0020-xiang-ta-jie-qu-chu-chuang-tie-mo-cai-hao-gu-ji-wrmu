from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from core.access import identity, issue
from core.db import transaction
from core.errors import DomainError
from core.passwords import verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
DUMMY_PASSWORD = "00000000000000000000000000000000:" + "0" * 64


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)


@router.post("/login")
def login(body: Login, request: Request):
    with transaction() as conn:
        user = conn.execute(
            "SELECT id, username, role, password FROM users WHERE username = %s AND active",
            (body.username,),
        ).fetchone()
    valid = verify_password(body.password, user["password"] if user else DUMMY_PASSWORD)
    if not valid or user is None:
        raise DomainError(401, "Invalid username or password")
    request.state.actor = user["username"]
    return {
        "access_token": issue(user),
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }


@router.get("/me")
def me(user=Depends(identity)):
    return user
