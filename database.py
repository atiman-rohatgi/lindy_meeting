# Connects to the Postgres database using the DATABASE_URL from .env and exposes a session dependency.

import os
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# initializes a pool of 1–10 reusable Postgres connections using the URL from .env
connection_pool = pool.SimpleConnectionPool(
    1,
    10,
    dsn=os.getenv("DATABASE_URL")
)

# checks out a connection from the pool, yields a RealDictCursor, then commits or rolls back and returns the connection
@contextmanager
def get_db():
    conn = connection_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield conn, cursor
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)
