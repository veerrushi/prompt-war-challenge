# Use official lightweight Python image
FROM python:3.11-slim

# Prevent .pyc files, enable unbuffered logs, and set default port
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# Create a non-root user and group for better security and maintainability
RUN addgroup --system appuser && adduser --system --group appuser

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer — only rebuilds when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/
COPY static/ ./static/

# Change ownership of the application files to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the port so container orchestrators can inspect it
EXPOSE $PORT

# Start the server — $PORT is injected by Render / Cloud Run at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
