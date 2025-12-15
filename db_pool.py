import os
from psycopg2 import pool
from contextlib import contextmanager

DATABASE_URL = os.environ.get('DATABASE_URL')

_connection_pool = None

def get_pool():
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(1, 5, DATABASE_URL)
    return _connection_pool

@contextmanager
def get_connection():
    conn = get_pool().getconn()
    try:
        yield conn
    finally:
        get_pool().putconn(conn)
