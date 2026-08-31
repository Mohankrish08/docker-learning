# 🐳 Class 3 (Basic) — One Image, Two Containers

**The idea:** an image is just a blueprint. What a container *does* is decided
when you start it — by the `command` you give it.

Here we build **one image** and run **two different containers** from it.

```
                 simple-app:v1
                  (ONE image)
                       │
            ┌──────────┴──────────┐
            │                     │
    python web.py          python writer.py
            │                     │
       ┌────▼────┐           ┌────▼────┐
       │  web    │           │ writer  │
       │ website │           │  loop   │
       └────┬────┘           └────┬────┘
            │                     │
            │   shared folder     │
            └──────► /data ◄──────┘
                 messages.txt
```

---

## What it does

| Container | What it does |
|-----------|--------------|
| **writer** | Every 5 seconds, writes one line into `/data/messages.txt`. No website. |
| **web** | A web page that shows that file. It only reads — it never writes. |

They never talk to each other. They just share a folder.

---

## The files

```
third-doc-image-basic/
├── writer.py            # container 1 — the loop
├── web.py               # container 2 — the website
├── requirements.txt     # flask
├── Dockerfile           # builds the ONE image
├── docker-compose.yml   # runs the TWO containers
└── README.md
```

---

## The code

### `writer.py` — container 1

```python
import time
from datetime import datetime

while True:
    line = f"Hello from the writer at {datetime.now():%H:%M:%S}"

    with open("/data/messages.txt", "a") as f:
        f.write(line + "\n")

    print("wrote:", line)
    time.sleep(5)
```

- `while True:` — runs forever. This container never finishes.
- `"a"` means **append** — add to the end of the file. If you used `"w"` it
  would erase the file every time.
- `time.sleep(5)` — wait 5 seconds, then go round again.

That is the whole container. No Flask, no port, no website.

### `web.py` — container 2

```python
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    with open("/data/messages.txt") as f:
        lines = f.readlines()

    return f"""
    <meta http-equiv="refresh" content="2">
    <h1>Messages: {len(lines)}</h1>
    <pre>{"".join(lines)}</pre>
    """

app.run(host="0.0.0.0", port=5000)
```

- Opens the same file the writer is writing to, and shows it.
- `<meta http-equiv="refresh" content="2">` — tells the browser to reload
  itself every 2 seconds, so you can watch new lines appear on their own.
- `host="0.0.0.0"` — listen on all addresses. If you used `127.0.0.1` the app
  would only accept connections from inside the container, and your browser
  could not reach it. **This trips up almost everyone once.**

---

## The Dockerfile

```dockerfile
FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web.py writer.py ./

CMD ["python", "web.py"]
```

- `FROM python:3.11-alpine` — start from a small Linux image with Python in it.
- `ENV PYTHONUNBUFFERED=1` — without this, `print()` output gets held in a
  buffer and `docker compose logs` shows you nothing for ages.
- `COPY web.py writer.py ./` — **both** files go into the image. Every container
  carries both scripts; each one only runs the script it is told to.
- `CMD` — the *default* command. Compose overrides it for the writer.

Notice the Dockerfile does not know anything about "web" or "writer" roles.
It just packs the files. The decision comes later.

---

## The compose file — where the magic is

```yaml
services:

  web:
    build: .
    image: simple-app:v1
    command: python web.py        # <-- makes it a website
    ports:
      - "5000:5000"
    volumes:
      - shared-data:/data

  writer:
    build: .
    image: simple-app:v1          # <-- SAME image
    command: python writer.py     # <-- makes it a writer
    volumes:
      - shared-data:/data

volumes:
  shared-data:
```

Read the two services side by side. Same `image:`. The **only** meaningful
difference is the `command:` line.

- `command:` replaces the `CMD` from the Dockerfile. This is the whole lesson.
- `ports: "5000:5000"` — left is the port on **your computer**, right is the port
  **inside the container**. The writer has no ports, because nothing needs to
  reach it. *A container does not have to be a server.*
- `volumes: shared-data:/data` — both containers get the same folder mounted at
  `/data`. That is how the file gets from one container to the other.

---

## How to run it

```bash
docker compose up -d --build
```

Then open **http://localhost:5000** in your browser and just watch. A new line
appears every 5 seconds, written by the *other* container.

To see the two containers:

```bash
docker compose ps
```

```
NAME                             IMAGE           COMMAND
third-doc-image-basic-web-1      simple-app:v1   "python web.py"
third-doc-image-basic-writer-1   simple-app:v1   "python writer.py"
```

**Same IMAGE column. Different COMMAND column.** That is the whole class in one
screen — worth pausing on.

---

## The demo to do in class

1. Open http://localhost:5000 and let it sit. Lines keep appearing.

2. Stop **only** the writer:
   ```bash
   docker compose stop writer
   ```
   The web page keeps working — but the lines stop growing. The website is fine;
   the thing feeding it is gone.

3. Start it again:
   ```bash
   docker compose start writer
   ```
   Lines start appearing again, right where they left off.

4. Prove there is only one image:
   ```bash
   docker images simple-app
   ```
   One row. Two containers were running from it.

---

## Clean up

```bash
docker compose down       # remove containers (the messages are kept)
docker compose down -v    # also delete the volume (messages are gone)
```

Try `down` then `up -d` — your old messages are still there, because the volume
survived. That is what volumes are for.

---

## Key points

| Thing | Meaning |
|-------|---------|
| **Image** | The blueprint. Built once. Does nothing on its own. |
| **Container** | A running copy of the image. You can run many. |
| **`command:`** | Decides what the container actually does. |
| **Volume** | A folder Docker keeps, shared between containers, survives them. |
| **`ports`** | `yourPC:container`. Only needed if something must reach in. |

> **One sentence to remember:**
> The image is the same. The `command` is what makes one container a website and
> the other a writer.

---

## Want the advanced version?

See [../third-doc-image/](../third-doc-image/) — the same idea built properly,
with a real job queue, a background worker, `ENTRYPOINT` + `APP_ROLE`, and
`--scale worker=3`. Good to show a student who asks *"what does a real one look
like?"*
