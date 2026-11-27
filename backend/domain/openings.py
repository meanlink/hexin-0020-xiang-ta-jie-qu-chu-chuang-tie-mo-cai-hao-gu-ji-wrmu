from core.errors import DomainError

GEOMETRY_FIELDS = (
    "exhibit", "finish_code", "width_mm", "height_mm", "bevel_left_mm", "bevel_right_mm",
    "bleed_mm", "pattern_axis", "allow_seam",
)


def get_window(conn, code, *, lock=False):
    query = "SELECT * FROM window_profiles WHERE code = %s"
    if lock:
        query += " FOR UPDATE"
    result = conn.execute(query, (code,)).fetchone()
    if result is None:
        raise DomainError(404, "window profile not found")
    return result


def add_window(conn, payload):
    result = conn.execute(
        """INSERT INTO window_profiles (code, exhibit, finish_code, width_mm, height_mm, bevel_left_mm,
                bevel_right_mm, bleed_mm, pattern_axis, allow_seam)
           VALUES (%(code)s,%(exhibit)s,%(finish_code)s,%(width_mm)s,%(height_mm)s,%(bevel_left_mm)s,
                   %(bevel_right_mm)s,%(bleed_mm)s,%(pattern_axis)s,%(allow_seam)s)
           ON CONFLICT (code) DO NOTHING RETURNING *""", payload,
    ).fetchone()
    if result is None:
        raise DomainError(409, "window code already registered")
    return result


def check_revision(window, expected):
    if window["revision"] != expected:
        raise DomainError(409, "window dimensions changed; measure and estimate the new revision")


def revise_window(conn, code, payload):
    current = get_window(conn, code, lock=True)
    check_revision(current, payload["expected_revision"])
    if all(current[name] == payload[name] for name in GEOMETRY_FIELDS):
        return current
    return conn.execute(
        """UPDATE window_profiles SET exhibit = %(exhibit)s, finish_code = %(finish_code)s,
             width_mm = %(width_mm)s, height_mm = %(height_mm)s, bevel_left_mm = %(bevel_left_mm)s,
             bevel_right_mm = %(bevel_right_mm)s, bleed_mm = %(bleed_mm)s, pattern_axis = %(pattern_axis)s,
             allow_seam = %(allow_seam)s, revision = revision + 1
           WHERE code = %(code)s RETURNING *""",
        {"code": code, **payload},
    ).fetchone()
