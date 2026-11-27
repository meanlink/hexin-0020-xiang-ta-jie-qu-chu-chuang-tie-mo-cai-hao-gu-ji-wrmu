from uuid import UUID

from fastapi import APIRouter, Depends

from core.access import allow
from core.db import transaction
from core.jobs import enqueue
from domain.allocation import issue_sheet, void_sheet
from domain.fit_geometry import solve_fit
from domain.inventory import get_roll
from domain.openings import check_revision, get_window
from domain.receipts import complete_cut, withdrawn_sheets
from domain.sheet_inputs import CompleteCut, NewEstimate, VoidCut
from domain.sheet_store import find_sheet, sheet_panels
from domain.tasks import ESTIMATE_CUT

router = APIRouter(tags=["裁切签发与核销"])


@router.post("/cut-estimates", dependencies=[Depends(allow("admin", "operator"))], status_code=202)
def estimate(body: NewEstimate):
    with transaction() as conn:
        window = get_window(conn, body.window_code)
        check_revision(window, body.window_revision)
        solve_fit(window, get_roll(conn, body.roll_code))
        return enqueue(conn, ESTIMATE_CUT, body.model_dump(mode="json"))


@router.get("/cut-sheets/{sheet_id}", dependencies=[Depends(allow("admin", "operator", "viewer"))])
def get_sheet(sheet_id: UUID):
    with transaction() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        sheet = find_sheet(conn, sheet_id)
        receipt = conn.execute("SELECT * FROM cut_receipts WHERE sheet_id = %s", (sheet_id,)).fetchone()
        return {
            **sheet,
            "panels": sheet_panels(conn, sheet_id),
            "receipt": receipt,
            "withdrawn_sheets": withdrawn_sheets(conn, sheet_id) if receipt else [],
        }


@router.post("/cut-sheets/{sheet_id}/issue", dependencies=[Depends(allow("admin"))])
def issue(sheet_id: UUID):
    with transaction() as conn:
        return issue_sheet(conn, sheet_id)


@router.post("/cut-sheets/{sheet_id}/complete")
def complete(sheet_id: UUID, body: CompleteCut, actor=Depends(allow("admin", "operator"))):
    with transaction() as conn:
        return complete_cut(conn, sheet_id, body.used_mm, actor["username"])


@router.post("/cut-sheets/{sheet_id}/void", dependencies=[Depends(allow("admin"))])
def void(sheet_id: UUID, body: VoidCut):
    with transaction() as conn:
        return void_sheet(conn, sheet_id, body.reason)
