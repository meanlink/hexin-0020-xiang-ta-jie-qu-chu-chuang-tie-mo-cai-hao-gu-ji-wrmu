from fastapi import APIRouter, Depends

from core.access import allow
from core.db import transaction
from domain.inventory import get_roll, ledger_view, register_roll
from domain.roll_inputs import AddRoll

router = APIRouter(prefix="/rolls", tags=["卷材余量"])


@router.get("", dependencies=[Depends(allow("admin", "operator", "viewer"))])
def rolls():
    with transaction() as conn:
        return [ledger_view(roll) for roll in conn.execute("SELECT * FROM film_rolls ORDER BY code LIMIT 100")]


@router.post("", dependencies=[Depends(allow("admin"))], status_code=201)
def add_roll(payload: AddRoll):
    with transaction() as conn:
        return register_roll(conn, payload.model_dump(mode="json"))


@router.get("/{code}", dependencies=[Depends(allow("admin", "operator", "viewer"))])
def roll_detail(code: str):
    with transaction() as conn:
        ledger = ledger_view(get_roll(conn, code))
        ledger["issued_queue"] = conn.execute(
            """SELECT id, window_code, allowance_mm, issued_at FROM cut_sheets
               WHERE roll_code = %s AND state = 'issued' ORDER BY issued_order""", (code,),
        ).fetchall()
        return ledger
