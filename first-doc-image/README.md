# 🐳 My First Docker App

A simple Flask API running inside Docker.

---

## File Structure

```
my-app/
├── app.py            → Flask web app (the actual code)
├── requirements.txt  → Python libraries needed
└── Dockerfile        → Instructions to build the image
```

---

## What Each File Does

| File | What it is |
|------|-----------|
| `app.py` | The Python Flask app. Returns JSON when you visit localhost:5000 |
| `requirements.txt` | Tells pip which libraries to install (flask) |
| `Dockerfile` | Recipe to build the Docker image, step by step |

---

## Dockerfile — Line by Line

```dockerfile
FROM python:3.11-alpine   # Start with a tiny Python base image
WORKDIR /app              # Set working folder inside container
COPY requirements.txt .   # Copy requirements file in
RUN pip install ...       # Install dependencies
COPY app.py .             # Copy your app code in
EXPOSE 5000               # Document that app uses port 5000
CMD ["python", "app.py"]  # Command to start the app
```

---

## Commands

```bash
# 1. Build the image
docker build -t my-app:v1 .

# 2. Run the container
docker run -d --name my-flask -p 5000:5000 my-app:v1

# 3. Test it → open browser at:
http://localhost:5000

# 4. See logs
docker logs my-flask

# 5. Stop and remove
docker rm -f my-flask
```

---

## Key Concepts

| Term | Simple meaning |
|------|---------------|
| **Image** | The blueprint (built once) |
| **Container** | The running app (from the blueprint) |
| **Port 5000:5000** | host:container — maps your PC port to container port |
| `-d` | Run in background |
| `--rm` | Auto-delete container when stopped |
| `:alpine` | Smallest possible base image |