# 🐳 Learning Docker

A hands-on Docker course, one folder per class. Each class builds on the one
before it — do them in order.

---

## The Classes

| # | Folder | Topic | The one idea to take away |
|---|--------|-------|---------------------------|
| 1 | [first-doc-image/](first-doc-image/) | Your first image | An **image** is a blueprint; a **container** is a running copy of it |
| 2 | [second-doc-image/](second-doc-image/) | Production-ready image | Gunicorn, health checks, env vars, `docker compose` |
| 3 | [third-doc-image-basic/](third-doc-image-basic/) | One image, two containers | What a container *does* is decided by the `command` you give it |

---

## Repository Structure

```
Docker/
├── README.md                 # you are here
│
├── first-doc-image/          # CLASS 1 — hello world
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── README.md
│
├── second-doc-image/         # CLASS 2 — production practices
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   ├── .gitignore
│   └── README.md
│
├── third-doc-image-basic/    # CLASS 3 — one image, two containers (teach this)
│   ├── writer.py             # container 1: writes a line every 5s
│   ├── web.py                # container 2: shows the file
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── README.md
```

---

## 🚀 Running Any Class

```bash
cd third-doc-image      
docker compose up -d --build
docker compose ps
docker compose logs -f
docker compose down
```

Class 1 has no compose file — build and run it directly:

```bash
cd first-doc-image
docker build -t my-app:v1 .
docker run -d --name my-flask -p 5000:5000 my-app:v1
```

---

## Concept Map

| Concept | Introduced in |
|---------|---------------|
| `FROM`, `WORKDIR`, `COPY`, `RUN`, `CMD` | Class 1 |
| Layer caching (deps before code) | Class 1 |
| Port mapping `-p host:container` | Class 1 |
| `EXPOSE`, `.dockerignore` | Class 1 |
| Gunicorn instead of the dev server | Class 2 |
| `HEALTHCHECK` | Class 2 |
| Environment variables / `.env` | Class 2 |
| `docker-compose.yml`, networks | Class 2 |
| `ENTRYPOINT` vs `CMD` | Class 3 |
| One image → many roles | Class 3 |
| Named volumes & shared state | Class 3 |
| `--scale`, graceful `SIGTERM` shutdown | Class 3 |
| Running as a non-root user | Class 3 |

---

## Handy Commands

```bash
docker ps -a                       # all containers, running or not
docker images                      # all images on this machine
docker logs -f <container>         # follow a container's output
docker exec -it <container> sh     # open a shell inside a running container
docker volume ls                   # list volumes
docker system df                   # how much disk Docker is using
docker system prune                # clean up stopped containers & unused data
```
