# Base Image
FROM python:3.11-slim

# Set Working Directory
WORKDIR /app

# Install Dependencies (Biological Requirements)
# Added 'requests' and others just in case
RUN pip install --no-cache-dir redis google-generativeai chromadb web3 requests

# Copy the Organism (Source Code)
COPY miso-worker ./miso-worker

# Environment Variables
ENV PYTHONUNBUFFERED=1

# THE V45 ENTRYPOINT: The Unified Organism
CMD ["python3", "miso-worker/app/organism.py"]
