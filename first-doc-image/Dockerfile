# Layer 1: Base Image
FROM python:3.11-alpine

# Layer 2: Set working dir
WORKDIR /first-doc-image

# Layer 3: Copy and Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layer 4: Copy Code
COPY app.py .

# Metadata
EXPOSE 5000

# Star the app
CMD ["python", "app.py"]