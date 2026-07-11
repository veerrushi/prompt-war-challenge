# Use official lightweight Python image
FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Default port — overridden by Render (10000) or GCP Cloud Run (8080) at runtime
ENV PORT=10000

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer — only rebuilds when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/
COPY static/ ./static/

# Expose the port so container orchestrators can inspect it
EXPOSE $PORT

# Start the server — $PORT is injected by Render / Cloud Run at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
