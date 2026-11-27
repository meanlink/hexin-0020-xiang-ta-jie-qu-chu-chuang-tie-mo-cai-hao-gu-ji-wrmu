from core.errors import DomainError


def get_roll(conn, code, *, lock=False):
    query = "SELECT * FROM film_rolls WHERE code = %s"
    if lock:
        query += " FOR UPDATE"
    roll = conn.execute(query, (code,)).fetchone()
    if roll is None:
        raise DomainError(404, "film roll not found")
    return roll


def usable_width(roll):
    return roll["width_mm"] - 2 * roll["edge_damage_mm"]


def available_length(roll):
    return roll["initial_length_mm"] - roll["consumed_mm"] - roll["reserved_mm"]


def ledger_view(roll):
    return {
        **roll,
        "usable_width_mm": usable_width(roll),
        "available_mm": available_length(roll),
        "remaining_physical_mm": roll["initial_length_mm"] - roll["consumed_mm"],
    }


def register_roll(conn, roll):
    result = conn.execute(
        """INSERT INTO film_rolls (code, finish_code, width_mm, edge_damage_mm, pattern,
                thickness_um, initial_length_mm)
           VALUES (%(code)s,%(finish_code)s,%(width_mm)s,%(edge_damage_mm)s,%(pattern)s,
                   %(thickness_um)s,%(initial_length_mm)s)
           ON CONFLICT (code) DO NOTHING RETURNING *""", roll,
    ).fetchone()
    if result is None:
        raise DomainError(409, "film roll code already registered")
    return ledger_view(result)


def account_for_cut(conn, code, *, released_mm, used_mm=0):
    return conn.execute(
        """UPDATE film_rolls SET reserved_mm = reserved_mm - %s, consumed_mm = consumed_mm + %s
           WHERE code = %s RETURNING *""",
        (released_mm, used_mm, code),
    ).fetchone()
