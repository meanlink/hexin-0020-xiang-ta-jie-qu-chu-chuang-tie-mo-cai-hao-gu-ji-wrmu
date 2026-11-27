from core.errors import DomainError
from domain.history import record_measured_loss
from domain.inventory import account_for_cut, ledger_view
from domain.openings import check_revision
from domain.sheet_store import locked_context
from domain.vocabulary import SheetState


def complete_cut(conn, sheet_id, used_mm, actor):
    sheet, window, roll = locked_context(conn, sheet_id)
    if sheet["state"] != SheetState.ISSUED:
        raise DomainError(409, "only an issued cut sheet can post a stock receipt")
    check_revision(window, sheet["window_revision"])
    first = conn.execute(
        "SELECT id FROM cut_sheets WHERE roll_code = %s AND state = 'issued' ORDER BY issued_order LIMIT 1",
        (roll["code"],),
    ).fetchone()
    if first["id"] != sheet_id:
        raise DomainError(409, "an older issued cut must leave this roll first")
    if used_mm < sheet["feed_mm"]:
        raise DomainError(409, "measured use is below the physical panel feed length")
    if used_mm > sheet["allowance_mm"]:
        raise DomainError(409, "measured use exceeds this cut sheet's reserved allowance")
    start = roll["consumed_mm"]
    reserve = sheet["allowance_mm"]
    loss = used_mm - sheet["feed_mm"]
    receipt = conn.execute(
        """INSERT INTO cut_receipts (sheet_id, segment_from_mm, segment_to_mm, measured_loss_mm,
                   released_reserve_mm, cut_by)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""",
        (sheet_id, start, start + used_mm, loss, reserve - used_mm, actor),
    ).fetchone()
    updated = account_for_cut(conn, roll["code"], released_mm=reserve, used_mm=used_mm)
    conn.execute("UPDATE cut_sheets SET state = 'cut' WHERE id = %s", (sheet_id,))
    record_measured_loss(conn, sheet, window, roll, loss)
    return {**receipt, "roll": ledger_view(updated)}
