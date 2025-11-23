# This is the new, secure Dockerfile
FROM python:3.10-slim

# Install base dependencies (git, curl) and GitHub CLI
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    gpg \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install gh -y

# --- Worker Setup ---
WORKDIR /app

# Copy and install worker dependencies (from the miso_worker directory)
COPY ./miso_worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# --- Test Repo Setup (This is the new, secure part) ---
# Create a separate directory for the MISO-Phoenix repo code
WORKDIR /src/miso-phoenix-repo

# Copy the *entire* MISO-Phoenix project into this directory
# (This assumes you run the `docker build` command from the MISO-Phoenix root)
COPY . /src/miso-phoenix-repo/

# Pre-install the repo's dependencies securely *during the build*
# (This assumes the requirements.txt is in the root)
RUN pip install --no-cache-dir -r requirements.txt

# Reset WORKDIR to the app and copy the worker script
WORKDIR /app
COPY ./miso_worker/worker.py /app/worker.py

# Set container user
RUN useradd --create-home appuser
USER appuser

# Run the worker
CMD ["python", "worker.py"]
