FROM python:3.12-slim

ENV PYTHONUNBUFFERED=True \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install system dependencies (sqlite3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . ./

# Create and switch to non-root user
RUN useradd -m appuser && chown -R appuser:appuser $APP_HOME
USER appuser

# Run the web service
CMD exec gunicorn --bind :$PORT --workers 1 --timeout 3600 -k uvicorn.workers.UvicornWorker --forwarded-allow-ips="*" main:app
