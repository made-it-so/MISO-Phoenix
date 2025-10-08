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
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...), collection_name: str = Form("default")):
    start_time = time.time()
    BATCH_SIZE = 100  # Process 100 chunks at a time
    
    try:
        contents = await file.read()
        text_content = contents.decode('utf-8')
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        if not chunks:
            return Response(status_code=status.HTTP_400_BAD_REQUEST, content="No text content found in file.")

        # Ensure the collection exists before we start batching
        async with httpx.AsyncClient() as client:
            await client.post(f"{CHROMA_URL}/api/v1/collections", json={"name": collection_name, "get_or_create": True})

        total_chunks_added = 0
        # Process the chunks in batches
        for i in range(0, len(chunks), BATCH_SIZE):
            batch_chunks = chunks[i:i + BATCH_SIZE]
            
            embeddings = []
            for chunk in batch_chunks:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    embedding_response = await client.post(f"{OLLAMA_BASE_URL}/api/embeddings", json={"model": "nomic-embed-text", "prompt": chunk})
                    embedding_response.raise_for_status()
                    embeddings.append(embedding_response.json()["embedding"])
            
            # Prepare data for ChromaDB, ensuring IDs are unique for each chunk
            ids = [f"{file.filename}-{total_chunks_added + j}" for j in range(len(batch_chunks))]
            metadatas = [{"filename": file.filename} for _ in batch_chunks]

            async with httpx.AsyncClient(timeout=60.0) as client:
                add_response = await client.post(
                    f"{CHROMA_URL}/api/v1/collections/{collection_name}/add",
                    json={"embeddings": embeddings, "documents": batch_chunks, "ids": ids, "metadatas": metadatas}
                )
                add_response.raise_for_status()
            
            total_chunks_added += len(batch_chunks)
            logger.info(f"Ingested batch {i//BATCH_SIZE + 1}, {total_chunks_added}/{len(chunks)} chunks processed.")

        return {
            "filename": file.filename,
            "collection_name": collection_name,
            "vectors_added": total_chunks_added,
            "processing_time_seconds": round(time.time() - start_time, 2)
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))

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

        context_str = "\n\n".join(context_chunks)
        prompt = f"Based ONLY on the following context, provide a concise answer to the user's question.\n\nContext:\n{context_str}\n\nQuestion: {request.query}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            generation_response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={"model": request.model_name, "prompt": prompt, "stream": False})
            generation_response.raise_for_status()
            answer = generation_response.json().get("response", "No answer could be generated.")

        return {
            "answer": answer.strip(),
            "sources": context_chunks,
            "processing_time_seconds": round(time.time() - start_time, 2)
        }
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))