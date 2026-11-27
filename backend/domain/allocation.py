from core.errors import DomainError
from domain.fit_geometry import solve_fit
from domain.inventory import account_for_cut, available_length
from domain.openings import check_revision
from domain.sheet_store import locked_context
from domain.vocabulary import SheetState


def issue_sheet(conn, sheet_id):
    sheet, window, roll = locked_context(conn, sheet_id)
    if sheet["state"] != SheetState.DRAFT:
        raise DomainError(409, "only a draft cut sheet can be issued")
    check_revision(window, sheet["window_revision"])
    fresh_fit = solve_fit(window, roll)
    if fresh_fit != sheet["geometry"]:
        raise DomainError(409, "roll width or cut geometry changed; estimate again")
    if conn.execute(
        "SELECT 1 FROM cut_sheets WHERE window_code = %s AND state = 'issued'", (window["code"],),
    ).fetchone():
        raise DomainError(409, "this window already has an issued cut sheet")
    if available_length(roll) < sheet["allowance_mm"]:
        raise DomainError(409, "unreserved roll length cannot cover this measured cut allowance")
    conn.execute(
        "UPDATE film_rolls SET reserved_mm = reserved_mm + %s WHERE code = %s",
        (sheet["allowance_mm"], roll["code"]),
    )
    return conn.execute(
        """UPDATE cut_sheets SET state = 'issued', issued_at = now(),
              issued_order = nextval('cut_sheet_issue_order')
           WHERE id = %s RETURNING *""", (sheet_id,),
    ).fetchone()


def void_sheet(conn, sheet_id, reason):
    sheet, _, roll = locked_context(conn, sheet_id)
    if sheet["state"] not in (SheetState.DRAFT, SheetState.ISSUED):
        raise DomainError(409, "only draft or issued cut sheets can be voided")
    if sheet["state"] == SheetState.ISSUED:
        account_for_cut(conn, roll["code"], released_mm=sheet["allowance_mm"])
    return conn.execute(
        "UPDATE cut_sheets SET state = 'void', void_reason = %s WHERE id = %s RETURNING *",
        (reason, sheet_id),
    ).fetchone()
