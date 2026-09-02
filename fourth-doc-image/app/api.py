
import logging
import os

from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider

from app import db, queue
from app.config import DEBUG, PORT

logging.basicConfig(level=logging.INFO, format="[api] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class ISOJSON(DefaultJSONProvider):
    def default(self, obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return super().default(obj)


app = Flask(__name__)
app.json = ISOJSON(app)

db.init_db()
queue.wait_until_ready()


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "service": "task-api",
            "role": "api",
            "container": os.getenv("HOSTNAME", "unknown"),
            "hint": "POST /api/jobs with {\"text\": \"hello\"} to queue work",
        }
    ), 200


@app.route("/api/jobs", methods=["POST"])
def create_job():
    """Queue a job. Returns in milliseconds — the worker does the real work."""
    data = request.get_json(silent=True) or {}
    text = data.get("text")

    if not text or len(text.strip()) < 2:
        return jsonify({"error": "Field 'text' is required (min 2 chars)"}), 400

    # 1. Write it down (durable). 2. Announce it (fast).
    # If step 2 fails, the job is still safe — a worker's idle sweep finds it.
    job_id = db.enqueue(text.strip())
    queue.announce(job_id)
    logger.info("queued job %s", job_id)

    # 202 Accepted = "I took your request, it is not finished yet"
    return jsonify({"id": job_id, "status": "pending"}), 202


@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def read_job(job_id):
    """Poll a single job to watch it go pending -> processing -> done."""
    job = db.get_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200


@app.route("/api/jobs", methods=["GET"])
def read_jobs():
    return jsonify({"jobs": db.list_jobs(), "counts": db.stats()}), 200


@app.route("/health", methods=["GET"])
def health():
    db_ok = db.ping()
    queue_ok = queue.ping()
    healthy = db_ok and queue_ok

    body = {
        "status": "healthy" if healthy else "degraded",
        "checks": {"postgres": db_ok, "redis": queue_ok},
        "workers_alive": queue.live_workers(),
        "queue_depth": queue.depth(),
    }
    return jsonify(body), (200 if healthy else 503)


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error("server error: %s", error)
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Only used for local dev. In Docker, Gunicorn runs the app instead.
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
