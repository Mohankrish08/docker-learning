FROM python:3.11-alpine

# show print() output in `docker compose logs` straight away
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# BOTH files go in the image. Each container runs only one of them.
COPY web.py writer.py ./

# the default. docker-compose.yml overrides it for the writer.
CMD ["python", "web.py"]
