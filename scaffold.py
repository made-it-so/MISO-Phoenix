import os
from pathlib import Path

# This script builds the entire MISO project structure and files.
# It is the single source of truth for the project's foundation.

# --- Project Structure and File Contents ---
# The keys are the file paths, and the values are the file contents.
PROJECT_FILES = {
    "docker-compose.yml": """
version: '3.8'

services:
  nginx:
    image: miso-10-8-2025-nginx
    build:
      context: ./nginx
      dockerfile: Dockerfile
    ports:
      - "8888:80"
    networks:
      - miso-net
    depends_on:
      - backend

  backend:
    image: miso-10-8-2025-backend
    build:
      context: ./backend
      dockerfile: Dockerfile
    networks:
      - miso-net
    environment:
      - CHROMA_HOST=chromadb
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      chromadb:
        condition: service_healthy

  chromadb:
    image: ghcr.io/chroma-core/chroma:0.5.0
    networks:
      - miso-net
    volumes:
      - chroma_data:/chroma/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 5s
      timeout: 10s
      retries: 5

  ollama:
    image: ollama/ollama
    networks:
      - miso-net
    volumes:
      - ollama_data:/root/.ollama

networks:
  miso-net:
    driver: bridge

volumes:
  chroma_data:
    driver: local
  ollama_data:
    driver: local
""",
    "backend/Dockerfile": """
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    "backend/requirements.txt": """
fastapi
uvicorn
python-dotenv
httpx
langchain-text-splitters
pydantic
""",
    "backend/main.py": """
import os
import httpx
import logging
import time
from fastapi import FastAPI, Response, status, UploadFile, File, Form
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from typing import List, Dict

# --- Configuration & Models ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_URL = f"http://{CHROMA_HOST}:8000"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

class ChatRequest(BaseModel):
    collection_name: str
    query: str
    model_name: str = "llama3:8b"

# --- API Endpoints ---
@app.get("/")
def read_root(): return {"message": "MISO Backend is running."}

@app.get("/health", status_code=status.HTTP_200_OK)
def perform_health_check(response: Response):
    try:
        httpx.get(f"{CHROMA_URL}/api/v1/heartbeat").raise_for_status()
        httpx.get(OLLAMA_BASE_URL).raise_for_status()
        return {"status": "ok", "chromadb": "ok", "ollama": "ok"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...), collection_name: str = Form("default")):
    start_time = time.time()
    try:
        contents = await file.read(); text_content = contents.decode('utf-8')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        async with httpx.AsyncClient() as client:
            await client.post(f"{CHROMA_URL}/api/v1/collections", json={"name": collection_name, "get_or_create": True})
        embeddings = []
        for chunk in chunks:
            async with httpx.AsyncClient(timeout=60.0) as client:
                embedding_response = await client.post(f"{OLLAMA_BASE_URL}/api/embeddings", json={"model": "nomic-embed-text", "prompt": chunk})
                embedding_response.raise_for_status()
                embeddings.append(embedding_response.json()["embedding"])
        async with httpx.AsyncClient(timeout=60.0) as client:
            add_response = await client.post(
                f"{CHROMA_URL}/api/v1/collections/{collection_name}/add",
                json={"embeddings": embeddings, "documents": chunks, "ids": [f"{file.filename}-{i}" for i in range(len(chunks))],"metadatas": [{"filename": file.filename} for _ in chunks]}
            )
            add_response.raise_for_status()
        return {"filename": file.filename, "collection_name": collection_name, "vectors_added": len(chunks), "processing_time_seconds": round(time.time() - start_time, 2)}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}"); return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))

@app.post("/chat")
async def chat_with_collection(request: ChatRequest):
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            embedding_response = await client.post(f"{OLLAMA_BASE_URL}/api/embeddings", json={"model": "nomic-embed-text", "prompt": request.query})
            embedding_response.raise_for_status()
            query_embedding = embedding_response.json()["embedding"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            query_response = await client.post(
                f"{CHROMA_URL}/api/v1/collections/{request.collection_name}/query",
                json={"query_embeddings": [query_embedding], "n_results": 3, "include": ["documents", "distances"]}
            )
            query_response.raise_for_status()
            results = query_response.json()
            context_chunks = results.get("documents", [[]])[0]
        context_str = "\\n\\n".join(context_chunks)
        prompt = f"Based ONLY on the following context, provide a concise answer to the user's question.\\n\\nContext:\\n{context_str}\\n\\nQuestion: {request.query}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            generation_response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": request.model_name, "prompt": prompt, "stream": False})
            generation_response.raise_for_status()
            answer = generation_response.json().get("response", "No answer could be generated.")
        return {"answer": answer.strip(), "sources": context_chunks, "processing_time_seconds": round(time.time() - start_time, 2)}
    except Exception as e:
        logger.error(f"Chat failed: {e}"); return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
""",
    "nginx/Dockerfile": """
FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
""",
    "nginx/nginx.conf": """
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
}

def main():
    """Main function to create the project structure."""
    print("--- 🤖 Starting Project Scaffolding ---")
    root = Path.cwd()
    
    for file_path, content in PROJECT_FILES.items():
        full_path = root / file_path
        # Ensure the parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # Write the file content
        full_path.write_text(content.strip())
        print(f"✅ Created: {file_path}")
        
    print("--- 🎉 Scaffolding Complete! ---")
    print("Run 'Get-ChildItem -Recurse' to verify the structure.")

if __name__ == "__main__":
    main()