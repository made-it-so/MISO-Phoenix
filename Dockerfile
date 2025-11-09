FROM python:3.10-slim

WORKDIR /app

# Install git binary
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install all Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full autonomous application
COPY miso_main.py .

EXPOSE 5000
RUN useradd --no-log-init -u 1001 appuser
USER appuser

# --- THIS IS THE FIX ---
# Removed --preload. This will run a scheduler in each worker.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "miso_main:app"]
