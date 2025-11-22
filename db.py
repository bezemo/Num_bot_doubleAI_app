import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import settings

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password
    )
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    date_str TEXT NOT NULL,
                    mode TEXT NOT NULL CHECK (mode IN ('default', 'deep', 'master')),
                    report_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date_mode ON reports (user_id, date_str, mode);
            """)
            conn.commit()

def get_cached_report(user_id: int, date_str: str, mode: str) -> str | None:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT report_text FROM reports WHERE user_id = %s AND date_str = %s AND mode = %s;",
                (user_id, date_str, mode)
            )
            row = cur.fetchone()
            return row["report_text"] if row else None

def save_report(user_id: int, date_str: str, mode: str, report_text: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reports (user_id, date_str, mode, report_text) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;",
                (user_id, date_str, mode, report_text)
            )
            conn.commit()