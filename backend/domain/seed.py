from domain.fixtures import ROLLS, WINDOWS, historical_scraps


def seed(conn):
    with conn.cursor() as cursor:
        cursor.executemany(
            """INSERT INTO window_profiles (code, exhibit, finish_code, width_mm, height_mm,
                  bevel_left_mm, bevel_right_mm, bleed_mm, pattern_axis, allow_seam)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING""",
            WINDOWS,
        )
        cursor.executemany(
            """INSERT INTO film_rolls (code, finish_code, width_mm, edge_damage_mm,
                                     pattern, thickness_um, initial_length_mm)
               VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (code) DO NOTHING""",
            ROLLS,
        )
        cursor.executemany(
            """INSERT INTO scrap_observations (observation_code, feed_mm, usable_width_mm,
                    cross_web_mm, bevel_mm, thickness_um, panels, loss_mm)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (observation_code) DO NOTHING""",
            list(historical_scraps()),
        )
