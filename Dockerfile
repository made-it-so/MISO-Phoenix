# BASE: Hardened Python 3.12
FROM python:3.12-slim-bookworm

# METADATA
LABEL maintainer="MISO Corp"
LABEL version="1.0-Enterprise"

# ENV
ENV PYTHONUNBUFFERED=1

# --- THE FIX: Install UV via Direct Copy ---
# We copy the binary from the official image. No curl needed.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# DEPENDENCIES
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# INSTALLATION
COPY miso-worker/requirements.txt .
# Ensure Streamlit is included for the dashboard
RUN echo "streamlit" >> requirements.txt
# Install dependencies into the system python (since we are in a container)
RUN uv pip install --system -r requirements.txt

# COPY SOURCE
COPY miso-worker/app ./app
COPY miso_cli.py .

# INTERFACE
EXPOSE 8501 8000

# STARTUP SCRIPT
RUN echo '#!/bin/bash\nnohup python3 app/worker.py > worker.log 2>&1 &\nnohup python3 app/executive.py > exec.log 2>&1 &\nstreamlit run app/admin_console.py --server.port 8501 --server.address 0.0.0.0\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
