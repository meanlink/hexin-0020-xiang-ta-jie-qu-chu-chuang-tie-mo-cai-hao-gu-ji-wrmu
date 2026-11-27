from fastapi import APIRouter, Depends

from core.access import allow
from core.db import transaction
from domain.fit_geometry import solve_fit
from domain.inventory import get_roll
from domain.openings import add_window, get_window, revise_window
from domain.vocabulary import Code
from domain.window_inputs import NewWindow, ReviseWindow

router = APIRouter(prefix="/windows", tags=["窗格与可裁校核"])


@router.get("", dependencies=[Depends(allow("admin", "operator", "viewer"))])
def windows():
    with transaction() as conn:
        return conn.execute("SELECT * FROM window_profiles ORDER BY code LIMIT 100").fetchall()


@router.post("", dependencies=[Depends(allow("admin", "operator"))], status_code=201)
def create_window(payload: NewWindow):
    with transaction() as conn:
        return add_window(conn, payload.model_dump(mode="json"))


@router.get("/{code}", dependencies=[Depends(allow("admin", "operator", "viewer"))])
def detail(code: str):
    with transaction() as conn:
        return get_window(conn, code)


@router.put("/{code}", dependencies=[Depends(allow("admin", "operator"))])
def revise(code: str, payload: ReviseWindow):
    with transaction() as conn:
        return revise_window(conn, code, payload.model_dump(mode="json"))


@router.get("/{code}/fit", dependencies=[Depends(allow("admin", "operator", "viewer"))])
def preview_fit(code: str, roll_code: Code):
    with transaction() as conn:
        window = get_window(conn, code)
        return {"window_revision": window["revision"], **solve_fit(window, get_roll(conn, roll_code))}
