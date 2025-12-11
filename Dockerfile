FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (needed for some python libs)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application
COPY app ./app

# Expose Port
EXPOSE 8000

# Start Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
