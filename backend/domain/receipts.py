from core.errors import DomainError
from domain.history import record_measured_loss
from domain.inventory import account_for_cut, available_length, ledger_view
from domain.openings import check_revision
from domain.sheet_store import locked_context
from domain.vocabulary import SheetState

WITHDRAWAL_REASON = "withdrawn to cover the measured over-cut on cut sheet {sheet_id}"


def withdrawn_sheets(conn, receipt_sheet_id):
    return conn.execute(
        """SELECT w.withdrawn_sheet_id AS sheet_id, s.window_code, w.withdrawn_order AS issued_order,
                  w.released_reserve_mm
           FROM cut_withdrawals w JOIN cut_sheets s ON s.id = w.withdrawn_sheet_id
           WHERE w.receipt_sheet_id = %s ORDER BY w.withdrawn_order""",
        (receipt_sheet_id,),
    ).fetchall()


def _withdraw_tail(conn, roll, head, needed_mm):
    """Free up the over-cut length: spend unreserved stock first, then retract issued
    sheets from the roll queue's tail one at a time, stopping as soon as enough frees up.
    The roll row is already locked, so the remaining sheets keep their original order."""
    updated = roll
    if available_length(updated) >= needed_mm:
        return updated, []
    tail = conn.execute(
        """SELECT id, window_code, allowance_mm, issued_order FROM cut_sheets
           WHERE roll_code = %s AND state = 'issued' AND issued_order > %s
           ORDER BY issued_order DESC""",
        (roll["code"], head["issued_order"]),
    ).fetchall()
    withdrawn = []
    for queued in tail:
        if available_length(updated) >= needed_mm:
            break
        conn.execute(
            "UPDATE cut_sheets SET state = 'void', void_reason = %s WHERE id = %s",
            (WITHDRAWAL_REASON.format(sheet_id=queued["id"]), queued["id"]),
        )
        updated = account_for_cut(conn, roll["code"], released_mm=queued["allowance_mm"])
        withdrawn.append({
            "sheet_id": queued["id"],
            "window_code": queued["window_code"],
            "issued_order": queued["issued_order"],
            "released_reserve_mm": queued["allowance_mm"],
        })
    if available_length(updated) < needed_mm:
        raise DomainError(
            409, "roll remaining length cannot cover the measured cut even after withdrawing queued sheets",
        )
    return updated, withdrawn


def _replay(conn, sheet, used_mm, roll):
    """A retried posting returns the settled receipt without repeating any withdrawal
    or writing a second observation."""
    receipt = conn.execute(
        "SELECT * FROM cut_receipts WHERE sheet_id = %s", (sheet["id"],),
    ).fetchone()
    if receipt is None:
        raise DomainError(409, "cut sheet is closed but has no stock receipt")
    posted = receipt["segment_to_mm"] - receipt["segment_from_mm"]
    if used_mm != posted:
        raise DomainError(409, "this cut sheet already posted a different measured length")
    return {
        **receipt,
        "overrun_mm": max(posted - sheet["allowance_mm"], 0),
        "withdrawn_sheets": withdrawn_sheets(conn, sheet["id"]),
        "roll": ledger_view(roll),
    }


def complete_cut(conn, sheet_id, used_mm, actor):
    sheet, window, roll = locked_context(conn, sheet_id)
    if sheet["state"] == SheetState.CUT:
        return _replay(conn, sheet, used_mm, roll)
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

    overrun = max(used_mm - sheet["allowance_mm"], 0)
    _, withdrawn = _withdraw_tail(conn, roll, sheet, overrun)

    start = roll["consumed_mm"]
    loss = used_mm - sheet["feed_mm"]
    receipt = conn.execute(
        """INSERT INTO cut_receipts (sheet_id, segment_from_mm, segment_to_mm, measured_loss_mm,
                   released_reserve_mm, cut_by)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""",
        (sheet_id, start, start + used_mm, loss, max(sheet["allowance_mm"] - used_mm, 0), actor),
    ).fetchone()
    for queued in withdrawn:
        conn.execute(
            """INSERT INTO cut_withdrawals (receipt_sheet_id, withdrawn_sheet_id, withdrawn_order,
                   released_reserve_mm) VALUES (%s,%s,%s,%s)""",
            (sheet_id, queued["sheet_id"], queued["issued_order"], queued["released_reserve_mm"]),
        )
    updated = account_for_cut(conn, roll["code"], released_mm=sheet["allowance_mm"], used_mm=used_mm)
    conn.execute("UPDATE cut_sheets SET state = 'cut' WHERE id = %s", (sheet_id,))
    record_measured_loss(conn, sheet, window, roll, loss)
    return {
        **receipt,
        "overrun_mm": overrun,
        "withdrawn_sheets": withdrawn,
        "roll": ledger_view(updated),
    }
