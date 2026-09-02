import logging
import time

import redis

from app.config import HEARTBEAT_TTL, QUEUE_NAME, REDIS_URL, STARTUP_TIMEOUT

logger = logging.getLogger(__name__)

# decode_responses=True -> get str back instead of bytes.
client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def wait_until_ready():
    """Same retry logic as Postgres: healthy != instantly usable."""
    deadline = time.time() + STARTUP_TIMEOUT
    while True:
        try:
            client.ping()
            logger.info("redis ready")
            return
        except redis.RedisError as exc:
            if time.time() >= deadline:
                raise
            logger.warning("redis not ready (%s), retrying...", exc)
            time.sleep(1)


def ping():
    """Used by /health."""
    try:
        return client.ping()
    except redis.RedisError:
        return False


# ---------- the queue itself ----------

def announce(job_id):
    client.rpush(QUEUE_NAME, job_id)


def wait_for_job(timeout):
    item = client.blpop(QUEUE_NAME, timeout=timeout)
    return int(item[1]) if item else None


def depth():
    """How many jobs are waiting. This is THE number to autoscale on."""
    try:
        return client.llen(QUEUE_NAME)
    except redis.RedisError:
        return None


# ---------- the worker roll-call ----------

def heartbeat(worker_id):
    """Say 'I am alive' for the next HEARTBEAT_TTL seconds.

    SETEX = set with an expiry. If this worker is killed, the key simply
    expires and it disappears from the roll-call. No cleanup job needed.
    """
    client.setex(f"worker:{worker_id}", HEARTBEAT_TTL, str(time.time()))


def live_workers():
    """Which workers are currently alive.

    scan_iter, not KEYS: KEYS blocks the whole Redis server while it walks
    every key. It is fine on your laptop and an outage in production.
    """
    try:
        return sorted(k.split(":", 1)[1] for k in client.scan_iter("worker:*"))
    except redis.RedisError:
        return []
