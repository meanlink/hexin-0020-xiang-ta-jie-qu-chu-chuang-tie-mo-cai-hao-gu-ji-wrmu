from uuid import uuid4

from psycopg.types.json import Jsonb

from core.errors import DomainError
from domain.inventory import get_roll
from domain.openings import get_window


def find_sheet(conn, sheet_id):
    row = conn.execute("SELECT * FROM cut_sheets WHERE id = %s", (sheet_id,)).fetchone()
    if row is None:
        raise DomainError(404, "cut sheet not found")
    return row


def locked_context(conn, sheet_id):
    pending = find_sheet(conn, sheet_id)
    window = get_window(conn, pending["window_code"], lock=True)
    roll = get_roll(conn, pending["roll_code"], lock=True)
    return find_sheet(conn, sheet_id), window, roll


def sheet_panels(conn, sheet_id):
    return conn.execute(
        "SELECT panel_no, cross_web_mm, advance_mm FROM cut_panels WHERE sheet_id = %s ORDER BY panel_no", (sheet_id,),
    ).fetchall()


def insert_draft(conn, window, roll, fit, loss_mm, metrics):
    sheet_id = uuid4()
    conn.execute(
        """INSERT INTO cut_sheets (id, window_code, window_revision, roll_code, orientation,
              usable_width_mm, feed_mm, predicted_loss_mm, allowance_mm, geometry, metrics)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (sheet_id, window["code"], window["revision"], roll["code"], fit["orientation"], fit["usable_width_mm"],
         fit["feed_mm"], loss_mm, fit["feed_mm"] + loss_mm, Jsonb(fit), Jsonb(metrics)),
    )
    with conn.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO cut_panels (sheet_id, panel_no, cross_web_mm, advance_mm) VALUES (%s,%s,%s,%s)",
            [(sheet_id, n, width, fit["advance_mm"]) for n, width in enumerate(fit["widths_mm"], 1)],
        )
    return sheet_id
