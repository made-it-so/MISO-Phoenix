FROM python:3.11-slim

# 1. INSTALL SYSTEM DEPENDENCIES
RUN apt-get update && apt-get install -y \
    docker.io \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. INSTALL PYTHON DEPENDENCIES
RUN pip install --no-cache-dir \
    redis \
    google-generativeai \
    chromadb \
    web3 \
    requests \
    numpy

# 3. COPY SOURCE CODE
COPY . /app

# 4. CONFIGURATION
ENV PYTHONUNBUFFERED=1
# CRITICAL FIX: Allow imports from the root /app folder
ENV PYTHONPATH=/app

# 5. ENTRYPOINT
CMD ["python3", "miso-worker/app/organism.py"]
