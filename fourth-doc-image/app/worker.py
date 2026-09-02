import logging
import os
import signal
import time

from app import db, queue
from app.config import BLOCK_TIMEOUT, JOB_DURATION

logging.basicConfig(level=logging.INFO, format="[worker] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# HOSTNAME is the container id — with --scale worker=3 you can see which one
# picked up which job.
WORKER_ID = os.getenv("HOSTNAME", "worker-1")

running = True


def stop(signum, _frame):
    global running
    logger.info("received signal %s, shutting down after current job", signum)
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def do_the_slow_work(text):
    """Pretend this is resizing an image / sending mail / building a report."""
    time.sleep(JOB_DURATION)
    return text.upper()[::-1]


def process(job):
    logger.info("picked up job %s: %r", job["id"], job["text"])
    try:
        result = do_the_slow_work(job["text"])
        db.complete_job(job["id"], result)
        logger.info("finished job %s -> %r", job["id"], result)
    except Exception as exc:                          # noqa: BLE001
        logger.error("job %s failed: %s", job["id"], exc)
        db.fail_job(job["id"], str(exc))


def main():
    db.init_db()
    queue.wait_until_ready()
    logger.info("worker %s started, waiting on the queue", WORKER_ID)

    while running:
        queue.heartbeat(WORKER_ID)

        # Sleep here until Redis wakes us. No CPU, no database queries.
        job_id = queue.wait_for_job(timeout=BLOCK_TIMEOUT)

        if job_id is None:
            # The queue went quiet. Use the idle moment to sweep Postgres for
            # jobs whose Redis announcement was lost (e.g. Redis restarted).
            # This is why the database, not the queue, is the source of truth.
            job = db.claim_next_pending(WORKER_ID)
            if job:
                logger.info("recovered orphaned job %s from postgres", job["id"])
                process(job)
            continue

        job = db.claim(job_id, WORKER_ID)
        if job is None:
            # Another worker got there first, or the job was already handled.
            logger.info("job %s was already claimed, skipping", job_id)
            continue

        process(job)

    logger.info("worker %s stopped", WORKER_ID)


if __name__ == "__main__":
    main()
