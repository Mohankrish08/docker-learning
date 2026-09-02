# 🐳 Fourth Docker Image — Real Services Behind Your App

**The lesson of this class:** a container that holds state is a liability.
Push every byte that matters out of your own containers and into services
built to keep it — then let Docker wire them together by name.

Class 3 had two containers sharing a **SQLite file on a volume**. It worked,
and it is the one thing in this repo that real production never does. This
class replaces that file with **Postgres** (the truth) and **Redis** (the
queue), and the app containers become completely disposable.

```
                    docker build
                         │
                         ▼
              ┌───────────────────────┐
              │  fourth-doc-image:v1  │   ← still ONE image of our own
              └───────────┬───────────┘
                          │
          ┌───────────────┴───────────────┐
   APP_ROLE=api                    APP_ROLE=worker
          │                               │
          ▼                               ▼
  ┌───────────────┐               ┌───────────────┐
  │  api          │               │  worker × N   │
  │  port 5000 ───┼─→ your laptop │  no port      │
  │  answers fast │               │  works slow   │
  └───┬───────┬───┘               └───┬───────┬───┘
      │       │                       │       │
      │       └───────────┐ ┌─────────┘       │
      │                   ▼ ▼                 │
      │            ┌───────────────┐          │
      │            │  queue :6379  │◄─────────┘   Redis — "there is work"
      │            │    (redis)    │
      │            └───────────────┘
      │
      │            ┌───────────────┐
      └───────────►│   db :5432    │◄─────────────  Postgres — the truth
                   │  (postgres)   │
                   └───────┬───────┘
                           │
                     named volume
                       (pgdata)
```

---

## 🎯 Why this matters (the business case)

Every business app eventually has an operation that takes minutes: month-end
payroll for 5,000 employees, a bulk attendance import, a year-long report.
Class 3 already moved that work off the request. This class makes it survive
real volume.

| Risk in class 3 | What it costs a business | Fixed by |
|---|---|---|
| SQLite allows **one writer at a time** | Two workers on payroll → lock errors, failed jobs, manual re-runs | Postgres |
| A shared file can be **corrupted mid-write** | Silent data loss with no recovery point — a compliance problem, not just a bug | Postgres |
| **Backups require stopping the app** | No nightly backup without downtime | Postgres |
| Both containers need the **same physical disk** | Your ceiling is one server, forever | Network access |
| Worker **polls every 2 seconds** | 20 workers = 600 pointless queries/minute, and up to 2s of latency per job | Redis |

Measured in this project: job pickup went from *up to 2000 ms* of polling
delay to **6 ms**.

---

## 📂 Project Structure

```
fourth-doc-image/
├── app/
│   ├── __init__.py       # makes 'app' a Python package
│   ├── config.py         # every setting from env vars — now URLs, not paths
│   ├── db.py             # ⭐ Postgres: the SOURCE OF TRUTH
│   ├── queue.py          # ⭐ Redis: the queue + worker roll-call
│   ├── api.py            # CONTAINER 1 — Flask API
│   └── worker.py         # CONTAINER 2 — blocks on the queue, no polling
├── entrypoint.sh         # decides api-or-worker from APP_ROLE
├── Dockerfile            # builds the ONE image (now python:3.11-slim)
├── docker-compose.yml    # ⭐ THE LESSON — four services wired together
├── requirements.txt      # flask, gunicorn, psycopg, redis
├── .dockerignore
├── .env.example          # credentials template (.env itself is gitignored)
├── .gitattributes        # forces LF endings on .sh (Windows fix)
├── .gitignore
└── README.md             # this file
```

---

## 🚀 Run It

```bash
cd fourth-doc-image
cp .env.example .env
docker compose up -d --build
```

Watch the boot order — this is the headline of the class:

```
task-db     Waiting
task-queue  Waiting
task-queue  Healthy      ← only now...
task-db     Healthy      ← ...are the dependencies actually usable
task-api    Starting     ← so our app starts here, not earlier
worker-1    Starting
```

Then:

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/api/jobs \
     -H "Content-Type: application/json" \
     -d '{"text":"process payroll"}'
curl http://localhost:5000/api/jobs/1
```

On Windows PowerShell use `curl.exe` (plain `curl` is an alias for
`Invoke-WebRequest`), and escape the inner quotes:

```powershell
curl.exe -X POST http://localhost:5000/api/jobs -H "Content-Type: application/json" -d '{\"text\":\"process payroll\"}'
```

---

## 🧠 The Four Concepts

### 1. Service discovery — containers find each other by NAME

There is not one IP address in this project. The connection string says:

```
postgresql://taskuser:taskpass@db:5432/tasks
                               ^^
                               the SERVICE NAME from docker-compose.yml
```

Docker runs a DNS server on every network. `db` resolves to whichever
container is currently that service. Restart it, get a new IP — nothing
breaks, because nothing ever knew the old one.

```bash
docker compose exec api python -c "import socket; print(socket.gethostbyname('db'))"
# 172.21.0.3   ← and you never needed to know that
```

### 2. `depends_on` — start order is NOT readiness

This is the mistake almost everyone makes once:

```yaml
depends_on:
  - db          # ❌ waits for the CONTAINER to start (~0.5s)
                #    Postgres accepts connections ~5s later.
                #    Your app boots, can't connect, and crash-loops.
```

```yaml
depends_on:
  db:
    condition: service_healthy    # ✅ waits for the HEALTHCHECK to pass
```

Which is why `db` defines one:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U taskuser -d tasks"]
```

**Belt and braces:** [`db.py`](app/db.py) *also* retries for 30 seconds on
boot. Compose guarantees order on your laptop; nothing guarantees it in
production. An app that cannot survive its database being briefly absent
will not survive a database upgrade either.

### 3. Publish vs. expose — who can reach what

Look at which services have a `ports:` key. Only `api` does.

| Service | `ports:` | Reachable from your laptop? | Reachable from `api`? |
|---|---|---|---|
| `api` | `5000:5000` | ✅ yes | — |
| `worker` | none | ❌ no | ✅ (same network) |
| `db` | none | ❌ **no** | ✅ (same network) |
| `queue` | none | ❌ **no** | ✅ (same network) |

Publishing your database port to the host is how databases end up on the
public internet. You don't need it — to inspect the data, go *through* Docker:

```bash
docker compose exec db psql -U taskuser -d tasks -c "SELECT id, status, worker_id FROM jobs;"
docker compose exec queue redis-cli LLEN jobs
```

Two networks enforce it further: `worker` is on `backend` only, so it has no
path to the host at all.

```bash
docker inspect fourth-doc-image-worker-1 --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
# fourth-doc-image_backend            ← backend only
```

### 4. Push, don't poll

Class 3's worker asked the database "any work?" every 2 seconds forever.
This one calls `BLPOP` — it *blocks*, using no CPU and sending no queries,
and Redis wakes exactly one worker the instant a job arrives.

```python
item = client.blpop(QUEUE_NAME, timeout=timeout)   # sleeps until work exists
```

The timeout is deliberate: coming up for air every 5 seconds is what lets the
worker notice `SIGTERM` and shut down cleanly before Docker's 10-second
`SIGKILL`.

---

## 🔬 Experiments Worth Doing

### Scale the workers

```bash
docker compose up -d --scale worker=3
for i in 1 2 3 4 5 6; do
  curl -s -X POST http://localhost:5000/api/jobs \
       -H "Content-Type: application/json" -d "{\"text\":\"job-$i\"}"
done
curl -s http://localhost:5000/api/jobs
```

Every job carries the `worker_id` that handled it — you will see all three
share the load. Six 3-second jobs finish in ~10s instead of ~18s.

`/health` also lists the live workers, and they come from Redis keys with a
TTL. Kill a worker and it vanishes from the roll-call on its own:

```bash
docker compose stop worker
sleep 15 && curl -s http://localhost:5000/health     # workers_alive: []
```

### Prove the database is the source of truth, not the queue

Redis is a *notification*. If it is wiped, the jobs are still safe:

```bash
docker compose stop worker
curl -s -X POST http://localhost:5000/api/jobs \
     -H "Content-Type: application/json" -d '{"text":"orphan test"}'

docker compose exec queue redis-cli FLUSHALL      # the announcement is gone
docker compose start worker
docker compose logs worker | grep recovered
# [worker] INFO recovered orphaned job 8 from postgres
```

That is what `claim_next_pending()` in [`db.py`](app/db.py) is for — an idle
sweep using `FOR UPDATE SKIP LOCKED`, the Postgres idiom for a work queue.
It is also why the API writes to Postgres *before* announcing on Redis.

### Prove the data outlives the containers

```bash
docker compose down          # containers destroyed, volumes kept
docker volume ls | grep fourth
docker compose up -d
curl -s http://localhost:5000/api/jobs        # your jobs are all still there
```

```bash
docker compose down -v       # ⚠️ -v DESTROYS the volumes. Data is gone.
```

That single flag is the difference between a restart and a data-loss incident.

### Break it on purpose

```bash
docker compose stop db
curl -i http://localhost:5000/health
# HTTP/1.1 503 SERVICE UNAVAILABLE
# {"status":"degraded","checks":{"postgres":false,"redis":true}}
```

A health check that only reports "my process is running" is nearly useless —
a process with no database serves nothing but errors. This one checks its
dependencies and returns **503**, so a load balancer stops sending it traffic.

---

## 🐘 Why `python:3.11-slim` and not `alpine`?

Class 3 used `python:3.11-alpine`. This one does not, and the reason is a
genuinely useful rule:

Alpine uses **musl** libc. Nearly every Python package ships pre-compiled
wheels for **glibc** only. So on Alpine, `pip install psycopg[binary]` finds
no wheel, falls back to compiling from source, and needs gcc plus a Postgres
dev toolchain — a much slower build and a *bigger* final image than the
"small" base was supposed to give you.

> **Alpine for pure-Python apps. Slim once real drivers appear.**

---

## 🧯 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `api` crash-loops on first boot | `depends_on` without `condition: service_healthy` | See concept 2 |
| `password authentication failed` | Changed `POSTGRES_PASSWORD` after the volume was created — the DB keeps the *old* one | `docker compose down -v` and rebuild (destroys data) |
| `could not translate host name "db"` | Service renamed, or it is not on the `backend` network | Check `networks:` on both services |
| `entrypoint.sh: not found` | CRLF line endings from Windows Git | Already handled by `.gitattributes` and the `sed` line in the Dockerfile |
| Jobs stay `pending` forever | No worker running | `docker compose ps`, then `docker compose logs worker` |
| Port 5000 already in use | Something else has it | Change to `"5001:5000"` in `docker-compose.yml` |

---

## ✅ What You Learned

| Concept | Why it matters |
|---|---|
| Third-party images (`postgres`, `redis`) | You rarely build the hard parts yourself |
| Service discovery by DNS name | No IPs, no config changes when containers move |
| `depends_on: condition: service_healthy` | Start order ≠ readiness — the classic crash-loop |
| Retry-on-boot in application code | Compose is not there to protect you in production |
| Publish vs. expose | Databases must not be reachable from the host |
| Multiple networks | The worker has no path to the outside world |
| Named volumes for real data | `down` keeps it, `down -v` destroys it |
| Dependency-aware health checks (503) | Load balancers can route around a broken container |
| Blocking queue instead of polling | Lower latency, lower cost, actually scalable |
| Secrets via `.env` (gitignored) | Credentials never belong in git |
| Base image choice (musl vs glibc) | "Smaller" is not automatically smaller |

---

## ➡️ Next

**Class 5 — multi-stage builds and image slimming.** This image is a few
hundred MB. Build-time tools do not belong in a runtime image; `docker history`
will show you exactly where the weight is.

Then **registries** — tag, push, and pull the image on another machine, which
is the moment it stops being local and becomes something you *ship*.
