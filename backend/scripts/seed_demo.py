import hashlib
import json
import os

from psycopg import sql

from core.bootstrap import migrate
from core.db import transaction
from core.passwords import encode_password
from domain.seed import seed


def demo():
    with transaction() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(884301)")
        for role in ("admin", "operator", "viewer"):
            found = conn.execute("SELECT 1 FROM users WHERE username=%s", (role,)).fetchone()
            if found is None:
                password = os.environ.get(f"DEMO_{role.upper()}_PASSWORD", f"{role}-hexin-demo")
                conn.execute(
                    "INSERT INTO users(username,password,role) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (role, encode_password(password), role),
                )
        seed(conn)
        tables = conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ).fetchall()
        counts = {}
        for table in tables:
            name = table["tablename"]
            if name in {"audit_events", "jobs", "schema_migrations"}:
                continue
            rows = conn.execute(sql.SQL(
                "SELECT to_jsonb(record)::text AS data FROM {} AS record ORDER BY 1"
            ).format(sql.Identifier(name))).fetchall()
            content = "\n".join(row["data"] for row in rows)
            counts[name] = {"rows": len(rows), "sha256": hashlib.sha256(content.encode()).hexdigest()}
        return counts


if __name__ == "__main__":
    migrate()
    print(json.dumps(demo(), ensure_ascii=False, sort_keys=True))
