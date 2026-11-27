FEATURES = ("feed_mm", "usable_width_mm", "cross_web_mm", "bevel_mm", "thickness_um", "panels")


def feature_values(window, roll, fit):
    return {
        "feed_mm": fit["feed_mm"],
        "usable_width_mm": fit["usable_width_mm"],
        "cross_web_mm": max(fit["widths_mm"]),
        "bevel_mm": window["bevel_left_mm"] + window["bevel_right_mm"],
        "thickness_um": roll["thickness_um"],
        "panels": len(fit["widths_mm"]),
    }


def observations(conn):
    return conn.execute(
        """SELECT observation_code, feed_mm, usable_width_mm, cross_web_mm, bevel_mm,
              thickness_um, panels, loss_mm FROM scrap_observations
           ORDER BY (source_sheet IS NOT NULL) DESC, observation_code
           LIMIT 600"""
    ).fetchall()


def record_measured_loss(conn, sheet, window, roll, loss):
    features = feature_values(window, roll, sheet["geometry"])
    conn.execute(
        """INSERT INTO scrap_observations (observation_code, source_sheet,
             feed_mm, usable_width_mm, cross_web_mm, bevel_mm, thickness_um, panels, loss_mm)
           VALUES (%(observation_code)s,%(source_sheet)s,%(feed_mm)s,%(usable_width_mm)s,
                   %(cross_web_mm)s,%(bevel_mm)s,%(thickness_um)s,%(panels)s,%(loss_mm)s)""",
        {"observation_code": f"LIVE-{sheet['id']}", "source_sheet": sheet["id"], **features, "loss_mm": loss},
    )
