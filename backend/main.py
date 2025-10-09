import os
import requests
import logging
import time
from fastapi import FastAPI, Response, status, UploadFile, File, Form
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

print("--- PYTHON SCRIPT STARTING ---")

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()
CHROMA_URL = f"http://chromadb:8000"
OLLAMA_URL = f"http://ollama:11434"
print("--- CONFIGURATION LOADED ---")

class ChatRequest(BaseModel):
    collection_name: str
    query: str
    model_name: str = "llama3:8b"

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "MISO Backend (Simplified) is running."}

@app.post("/ingest")
def ingest_document(file: UploadFile = File(...), collection_name: str = Form("default")):
    print(f"\n--- RECEIVED /ingest REQUEST for collection: {collection_name} ---")
    try:
        # 1. Create Collection in ChromaDB
        print("[INGEST] Step 1: Creating collection...")
        response = requests.post(f"{CHROMA_URL}/api/v1/collections", json={"name": collection_name})
        print(f"[INGEST] ChromaDB create collection response: {response.status_code}")
        response.raise_for_status()

        # 2. Read and Split Document
        print("[INGEST] Step 2: Reading and splitting file...")
        text_content = file.file.read().decode('utf-8')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        print(f"[INGEST] Document split into {len(chunks)} chunks.")

        # 3. Generate Embeddings for each chunk
        print("[INGEST] Step 3: Generating embeddings from Ollama...")
        embeddings = []
        for i, chunk in enumerate(chunks):
            print(f"[INGEST]   - Getting embedding for chunk {i+1}/{len(chunks)}")
            embed_response = requests.post(f"{OLLAMA_URL}/api/embed", json={"model": "all-minilm", "prompt": chunk})
            embed_response.raise_for_status()
            embeddings.append(embed_response.json()["embedding"])
        print("[INGEST] All embeddings generated.")

        # 4. Add to ChromaDB
        print("[INGEST] Step 4: Adding documents and embeddings to ChromaDB...")
        add_response = requests.post(
            f"{CHROMA_URL}/api/v1/collections/{collection_name}/add",
            json={
                "embeddings": embeddings,
                "documents": chunks,
                "ids": [f"{file.filename}-{i}" for i in range(len(chunks))]
            }
        )
        print(f"[INGEST] ChromaDB add response: {add_response.status_code}")
        add_response.raise_for_status()

        print("[INGEST] --- INGESTION SUCCEEDED ---")
        return {"status": "success", "vectors_added": len(chunks)}

    except Exception as e:
        print(f"[INGEST] --- INGESTION FAILED ---")
        print(f"ERROR: {repr(e)}")
        return Response(status_code=500, content=f"Internal Server Error: {repr(e)}")