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
def read_root():
    return {"message": "MISO Backend is running."}

@app.get("/health", status_code=status.HTTP_200_OK)
def perform_health_check(response: Response):
    try:
        httpx.get(f"{CHROMA_URL}/api/v1/heartbeat").raise_for_status()
        httpx.get(OLLAMA_BASE_URL).raise_for_status()
        return {"status": "ok", "chromadb": "ok", "ollama": "ok"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.error(f"Health check failed: {repr(e)}")
        return {"status": "error", "detail": str(e)}

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...), collection_name: str = Form("default")):
    start_time = time.time()
    try:
        contents = await file.read()
        text_content = contents.decode('utf-8')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        async with httpx.AsyncClient() as client:
            create_collection_response = await client.post(f"{CHROMA_URL}/api/v1/collections", json={"name": collection_name})
            create_collection_response.raise_for_status()
        
        embeddings = []
        for chunk in chunks:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # FINAL FIX: Switched to the 'all-minilm' model
                embedding_response = await client.post(f"{OLLAMA_BASE_URL}/api/embed", json={"model": "all-minilm", "prompt": chunk})
                embedding_response.raise_for_status()
                response_json = embedding_response.json()
                
                if "embedding" in response_json: # all-minilm uses the 'embedding' key (singular)
                    embeddings.append(response_json["embedding"])
                else:
                    raise KeyError("Ollama API response did not return a valid embedding vector.")

        async with httpx.AsyncClient(timeout=60.0) as client:
            add_response = await client.post(
                f"{CHROMA_URL}/api/v1/collections/{collection_name}/add",
                json={"embeddings": embeddings, "documents": chunks, "ids": [f"{file.filename}-{i}" for i in range(len(chunks))],"metadatas": [{"filename": file.filename} for _ in chunks]}
            )
            add_response.raise_for_status()
            
        return {"filename": file.filename, "collection_name": collection_name, "vectors_added": len(chunks), "processing_time_seconds": round(time.time() - start_time, 2)}
    except Exception as e:
        logger.error(f"Ingestion failed: {repr(e)}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))

@app.post("/chat")
async def chat_with_collection(request: ChatRequest):
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # FINAL FIX: Switched to the 'all-minilm' model
            embedding_response = await client.post(f"{OLLAMA_BASE_URL}/api/embed", json={"model": "all-minilm", "prompt": request.query})
            embedding_response.raise_for_status()
            response_json = embedding_response.json()

            if "embedding" in response_json: # all-minilm uses the 'embedding' key (singular)
                query_embedding = response_json["embedding"]
            else:
                raise KeyError("Ollama API response did not return a valid embedding vector for chat.")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            query_response = await client.post(
                f"{CHROMA_URL}/api/v1/collections/{request.collection_name}/query",
                json={"query_embeddings": [query_embedding], "n_results": 3, "include": ["documents", "distances"]}
            )
            query_response.raise_for_status()
            results = query_response.json()
            context_chunks = results.get("documents", [[]])[0]
        
        context_str = "\n\n".join(context_chunks)
        prompt = f"Based ONLY on the following context, provide a concise answer to the user's question.\n\nContext:\n{context_str}\n\nQuestion: {request.query}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            generation_response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": request.model_name, "prompt": prompt, "stream": False})
            generation_response.raise_for_status()
            answer = generation_response.json().get("response", "No answer could be generated.")
        
        return {"answer": answer.strip(), "sources": context_chunks, "processing_time_seconds": round(time.time() - start_time, 2)}
    except Exception as e:
        logger.error(f"Chat failed: {repr(e)}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))