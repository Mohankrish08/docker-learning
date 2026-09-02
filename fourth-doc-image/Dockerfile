# =====================================================================
#  ONE image. TWO containers. (Same trick as class 3.)
#  What changed: this image now talks to OTHER containers over the
#  network, so it carries a Postgres driver and a Redis client.
# =====================================================================

# Class 3 used python:3.11-alpine. This class switches to -slim, and the
# reason is worth knowing:
#
#   Alpine uses musl libc. Almost every Python package ships pre-compiled
#   wheels for glibc only, so on Alpine `pip install psycopg[binary]` finds
#   no wheel, falls back to compiling from source, and needs gcc + a
#   Postgres dev toolchain — a slower build and a BIGGER final image than
#   the "small" base was supposed to give you.
#
#   Rule of thumb: Alpine for pure-Python apps, slim once real drivers appear.
FROM python:3.11-slim

# Never write .pyc files; send logs straight to the terminal (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first — this layer is cached and only rebuilds when
# requirements.txt changes, not when you edit your Python code.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ ./app/
COPY entrypoint.sh .

# On Windows, Git may save entrypoint.sh with CRLF line endings, and the
# shell will then fail with "not found". Strip the \r and make it executable.
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Run as a non-root user (a container that is broken into should not be root).
# Note there is no `mkdir /data` any more: this image owns no state at all.
# Every byte that must survive now lives inside Postgres or Redis.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Documentation only. The worker container simply ignores it.
EXPOSE 5000

# Default role if you forget to pass one
ENV APP_ROLE=api

ENTRYPOINT ["./entrypoint.sh"]
