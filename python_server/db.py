from contextlib import contextmanager
import mysql.connector
from config import DB_CONFIG

@contextmanager
def get_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def fetch_all(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return rows

def execute_many(statements):
    with get_connection() as conn:
        cursor = conn.cursor()
        for query, params in statements:
            cursor.execute(query, params)
        conn.commit()
        cursor.close()
