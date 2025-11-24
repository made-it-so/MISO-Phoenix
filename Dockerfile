# BASE LAYER: Official Python 3.12 Slim (Security Hardened)
FROM python:3.12-slim-bookworm

# META-DATA
LABEL maintainer="MISO Corp"
LABEL version="1.0-Enterprise"
LABEL description="Autonomous Cloud Arbitrage Engine"

# ENVIRONMENT
ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PATH="/root/.cargo/bin:$PATH"

# SYSTEM DEPENDENCIES
RUN apt-get update && apt-get install -y --no-install-recommends     curl     build-essential     && rm -rf /var/lib/apt/lists/*

# INSTALL UV (The Speed Layer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# WORKDIR
WORKDIR /app

# INSTALL DEPENDENCIES (Cached Layer)
# We copy only requirements first to leverage Docker layer caching
COPY miso-worker/requirements.txt .
# Add streamlit for the dashboard
RUN echo "streamlit" >> requirements.txt
RUN uv pip install --system -r requirements.txt

# COPY SOURCE CODE
# We copy the entire worker directory into the container
COPY miso-worker/app ./app
COPY miso_cli.py .

# EXPOSE PORTS
# 8501: Admin Dashboard
# 8000: API Gateway
EXPOSE 8501 8000

# HEALTHCHECK
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# LAUNCHER (The Entrypoint)
# We create a script to launch the Dashboard AND the Worker
RUN echo '#!/bin/bash\nnohup python3 app/worker.py > worker.log 2>&1 &\nnohup python3 app/executive.py > exec.log 2>&1 &\nstreamlit run app/admin_console.py --server.port 8501 --server.address 0.0.0.0\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
