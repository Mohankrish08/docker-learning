import logging
import time

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import DATABASE_URL, STARTUP_TIMEOUT

logger = logging.getLogger(__name__)

pool = ConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=5, open=False)


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          BIGSERIAL   PRIMARY KEY,
    text        TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'pending',
    result      TEXT,
    worker_id   TEXT,
    attempts    INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- Makes "find me the oldest pending job" fast once the table is large.
CREATE INDEX IF NOT EXISTS jobs_pending_idx ON jobs (id) WHERE status = 'pending';
"""


def init_db():
    """Open the pool and create the table. Safe to call from both containers.

    Compose already waits for Postgres to report healthy, but we retry anyway:
    'the port is open' and 'the database is ready to serve you' are not the
    same instant, and in production nobody guarantees start order at all.
    """
    deadline = time.time() + STARTUP_TIMEOUT
    while True:
        try:
            pool.open()
            pool.wait(timeout=5)
            break
        except Exception as exc:                       # noqa: BLE001
            if time.time() >= deadline:
                raise
            logger.warning("postgres not ready (%s), retrying...", exc)
            time.sleep(1)

    with pool.connection() as conn:
        conn.execute(SCHEMA)
    logger.info("postgres ready")


def ping():
    """Used by /health. True only if we can actually run a query."""
    try:
        with pool.connection(timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:                                  # noqa: BLE001
        return False


# ---------- used by the API container ----------

def enqueue(text):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jobs (text) VALUES (%s) RETURNING id", (text,)
        )
        return cur.fetchone()[0]


def get_job(job_id):
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        return cur.fetchone()


def list_jobs(limit=20):
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT %s", (limit,))
        return cur.fetchall()


def stats():
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        return {status: n for status, n in cur.fetchall()}


# ---------- used by the WORKER container ----------

def claim(job_id, worker_id):
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE jobs
               SET status = 'processing',
                   worker_id = %s,
                   started_at = now(),
                   attempts = attempts + 1
             WHERE id = %s AND status = 'pending'
         RETURNING id, text
            """,
            (worker_id, job_id),
        )
        return cur.fetchone()


def claim_next_pending(worker_id):
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE jobs
               SET status = 'processing',
                   worker_id = %s,
                   started_at = now(),
                   attempts = attempts + 1
             WHERE id = (
                     SELECT id FROM jobs
                      WHERE status = 'pending'
                      ORDER BY id
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                   )
         RETURNING id, text
            """,
            (worker_id,),
        )
        return cur.fetchone()


def complete_job(job_id, result):
    with pool.connection() as conn:
        conn.execute(
            "UPDATE jobs SET status='done', result=%s, finished_at=now() WHERE id=%s",
            (result, job_id),
        )


def fail_job(job_id, error):
    with pool.connection() as conn:
        conn.execute(
            "UPDATE jobs SET status='failed', result=%s, finished_at=now() WHERE id=%s",
            (f"ERROR: {error}", job_id),
        )
