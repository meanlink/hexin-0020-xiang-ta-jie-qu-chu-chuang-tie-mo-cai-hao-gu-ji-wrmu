from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL


@contextmanager
def transaction():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn
