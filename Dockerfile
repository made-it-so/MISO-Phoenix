FROM python:3.11-slim

# System Dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Optimization: Use Disk for Temp Files
RUN mkdir -p /app/tmp
ENV TMPDIR=/app/tmp

# --- STEP 1: INSTALL TORCH (CPU) ---
# (Should be cached)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# --- STEP 2: INSTALL TRANSFORMERS ---
# (Should be cached)
RUN pip install --no-cache-dir transformers accelerate optimum

# --- STEP 3: INSTALL DATA SCIENCE ---
# (Should be cached)
RUN pip install --no-cache-dir numpy pandas scipy scikit-learn

# --- STEP 4: INSTALL VISION & AUDIO ---
# (Should be cached)
RUN pip install --no-cache-dir opencv-python-headless librosa soundfile openai-whisper

# --- STEP 4.5: INSTALL VECTOR DBs & LANGCHAIN (The Missing Piece) ---
RUN pip install --no-cache-dir \
    qdrant-client \
    chromadb \
    langchain \
    langchain-community \
    langchain-openai \
    langchain-anthropic \
    langchain-google-genai

# --- STEP 5: INSTALL LIGHTWEIGHT REQS ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy App Code
COPY . .
RUN rm -rf /app/tmp

# Command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
