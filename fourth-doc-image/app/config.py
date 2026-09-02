import os

# Which role should this container play? -> "api" or "worker"
APP_ROLE = os.getenv("APP_ROLE", "api")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://taskuser:taskpass@db:5432/tasks"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://queue:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "jobs")

# API settings
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False") == "True"

# Worker settings
JOB_DURATION = float(os.getenv("JOB_DURATION", 3))     # fake "slow work" time
BLOCK_TIMEOUT = int(os.getenv("BLOCK_TIMEOUT", 5))     # secs to wait on the queue
HEARTBEAT_TTL = int(os.getenv("HEARTBEAT_TTL", 15))    # secs a heartbeat stays alive

# How long to keep retrying Postgres/Redis on boot before giving up
STARTUP_TIMEOUT = int(os.getenv("STARTUP_TIMEOUT", 30))
