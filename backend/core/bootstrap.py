from pathlib import Path

from core.db import transaction

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


def migrate():
    with transaction() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(884300)")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        completed = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if path.name not in completed:
                conn.execute(path.read_text())
                conn.execute("INSERT INTO schema_migrations(name) VALUES (%s)", (path.name,))
