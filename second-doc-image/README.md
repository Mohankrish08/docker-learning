# 🐳 Second Docker Image — Flask API (Production-Ready)

A professional Flask API running inside Docker with best practices, proper error handling, and production configurations.

---

## 📂 Project Structure

```
second-doc-image/
├── app.py                  # Flask application with 5 endpoints
├── requirements.txt        # Python dependencies
├── Dockerfile              # Multi-stage Docker build with health checks
├── docker-compose.yml      # Docker Compose for easy orchestration
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

---

## 📋 What Each File Does

| File | Purpose |
|------|---------|
| **app.py** | Flask app with logging, error handling, 5 routes, and 2 error handlers |
| **requirements.txt** | Dependencies: Flask, python-dotenv, Gunicorn |
| **Dockerfile** | Optimized Alpine-based image with health checks & Gunicorn |
| **docker-compose.yml** | One-command deployment with networking & volumes |
| **.env.example** | Template for environment variables |
| **.gitignore** | Excludes Python cache, virtual env, .env files |

---

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Copy the environment template
cp .env.example .env

# 2. Build and run
docker-compose up -d

# 3. Test the API
curl http://localhost:5000

# 4. View logs
docker-compose logs -f web

# 5. Stop
docker-compose down
```

### Option 2: Using Docker CLI

```bash
# 1. Build the image
docker build -t second-doc-image:v1 .

# 2. Run the container
docker run -d \
  --name flask-app \
  -p 5000:5000 \
  -e DEBUG=False \
  -e PORT=5000 \
  second-doc-image:v1

# 3. Test it
curl http://localhost:5000

# 4. View logs
docker logs -f flask-app

# 5. Stop and remove
docker stop flask-app
docker rm flask-app
```

---

## 📡 API Endpoints

### 1. **GET** `/`
Health check — returns API status

**Response:**
```json
{
  "message": "Welcome to Docker API",
  "status": "running",
  "timestamp": "2026-08-26T12:34:56.789012"
}
```

### 2. **GET** `/api/hello/<name>`
Greet a user by name

**Example:**
```bash
curl http://localhost:5000/api/hello/John
```

**Response:**
```json
{
  "message": "Hello, John!",
  "status": "success"
}
```

### 3. **POST** `/api/data`
Receive and echo JSON data

**Example:**
```bash
curl -X POST http://localhost:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 30}'
```

**Response:**
```json
{
  "received": {"name": "Alice", "age": 30},
  "status": "success"
}
```

### 4. **GET** `/health`
Kubernetes/orchestration health check

**Response:**
```json
{
  "status": "healthy"
}
```

### Error Responses

**404 Not Found:**
```json
{
  "error": "Endpoint not found"
}
```

**400 Bad Request:**
```json
{
  "error": "Invalid request"
}
```

---

## 🔧 Environment Variables

Create a `.env` file from `.env.example`:

```env
DEBUG=False          # Set to True for development
PORT=5000           # Port to run the app on
```

---

## 📦 Dependencies Explained

| Package | Version | Purpose |
|---------|---------|---------|
| **Flask** | 3.0.0 | Web framework |
| **python-dotenv** | 1.0.0 | Load environment variables from .env |
| **Gunicorn** | 21.2.0 | Production WSGI server (replaces Flask dev server) |

---

## 🏗️ Dockerfile Breakdown

```dockerfile
FROM python:3.11-alpine AS base
# Alpine = smallest Python image (~150MB vs 900MB with full Python)

WORKDIR /app
# Set working directory inside container

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install dependencies without caching (saves image space)

COPY app.py .
# Copy application code

EXPOSE 5000
# Document which port the app uses

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
# Docker automatically restarts unhealthy containers

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "app:app"]
# Use Gunicorn (production-grade) instead of Flask dev server
```

---

## 📊 Key Improvements Over first-doc-image

| Feature | first-doc-image | second-doc-image |
|---------|-----------------|------------------|
| **Endpoints** | 1 (/) | 5 (/, /api/hello, /api/data, /health, errors) |
| **Error Handling** | None | Comprehensive try-catch & 404/500 handlers |
| **Logging** | None | Structured logging to track requests |
| **Production Server** | Flask dev | Gunicorn (4 workers) |
| **Health Checks** | None | Built-in Docker health check |
| **Environment Config** | Hardcoded | Configurable via .env |
| **Orchestration** | Manual CLI | docker-compose.yml included |
| **Dependencies** | Flask only | Flask + Gunicorn + python-dotenv |

---

## 🎯 Best Practices Implemented

✅ **Error Handling** — All routes have try-catch and proper HTTP status codes  
✅ **Logging** — INFO & ERROR logs for debugging  
✅ **Health Checks** — Docker can auto-restart failed containers  
✅ **Environment Variables** — No hardcoding of config  
✅ **Production WSGI** — Gunicorn instead of Flask dev server  
✅ **Minimal Image** — Alpine Linux base (fast & secure)  
✅ **Networking** — Docker Compose networks for multi-container setups  
✅ **Documentation** — Comprehensive README & comments in code  

---

## 🧪 Testing

### Test all endpoints:

```bash
# Health check
curl http://localhost:5000/health

# Greet endpoint
curl http://localhost:5000/api/hello/Docker

# POST data
curl -X POST http://localhost:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Test 404
curl http://localhost:5000/nonexistent

# View logs
docker-compose logs web
```

---

## 🛑 Stop & Clean Up

```bash
# Stop container (keeps image)
docker-compose stop

# Remove container & networks
docker-compose down

# Remove image too
docker rmi second-doc-image:v1
```

---

## 📚 Learn More

- [Flask Docs](https://flask.palletsprojects.com/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Gunicorn Docs](https://gunicorn.org/)
- [Docker Compose Docs](https://docs.docker.com/compose/)

---

**Created:** 2026-08-26  
**Status:** Production-Ready ✅
