import os
import requests
import logging
from fastapi import FastAPI, Response, status, UploadFile, File, Form
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

CHROMA_URL = "http://chromadb:8000"
TOGETHER_API_URL = "https://api.together.xyz/v1"
API_KEY = os.environ.get("TOGETHER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
EMBEDDING_MODEL = "togethercomputer/m2-bert-80M-8k-retrieval"
CHAT_MODEL = "meta-llama/Llama-3-8b-chat-hf"

class ChatRequest(BaseModel):
    collection_name: str
    query: str

@app.get("/")
def read_root(): return {"message": "MISO (Managed Backend) is operational."}

@app.post("/ingest")
def ingest_document(file: UploadFile = File(...), collection_name: str = Form("default")):
    try:
        requests.post(f"{CHROMA_URL}/api/v1/collections", json={"name": collection_name}).raise_for_status()
        chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_text(file.file.read().decode('utf-8'))
        embed_response = requests.post(f"{TOGETHER_API_URL}/embeddings", headers=HEADERS, json={"model": EMBEDDING_MODEL, "input": chunks})
        embed_response.raise_for_status()
        embeddings = [item['embedding'] for item in embed_response.json()['data']]
        requests.post(f"{CHROMA_URL}/api/v1/collections/{collection_name}/add", json={"embeddings": embeddings, "documents": chunks, "ids": [f"{file.filename}-{i}" for i in range(len(chunks))]}).raise_for_status()
        return {"filename": file.filename, "collection_name": collection_name, "vectors_added": len(chunks)}
    except Exception as e:
        logger.error(f"Ingestion failed: {repr(e)}"); return Response(status_code=500, content=f"Error: {repr(e)}")

@app.post("/chat")
def chat_with_collection(request: ChatRequest):
    try:
        embed_response = requests.post(f"{TOGETHER_API_URL}/embeddings", headers=HEADERS, json={"model": EMBEDDING_MODEL, "input": [request.query]})
        embed_response.raise_for_status()
        query_embedding = embed_response.json()['data'][0]['embedding']
        query_response = requests.post(f"{CHROMA_URL}/api/v1/collections/{request.collection_name}/query", json={"query_embeddings": [query_embedding], "n_results": 3, "include": ["documents"]})
        query_response.raise_for_status()
        context_chunks = query_response.json().get("documents", [[]])[0]
        context_str = "\n\n".join(context_chunks)
        prompt = f"Based ONLY on the following context, answer the user's question. Context: {context_str}\n\nQuestion: {request.query}"
        chat_response = requests.post(f"{TOGETHER_API_URL}/chat/completions", headers=HEADERS, json={"model": CHAT_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False})
        chat_response.raise_for_status()
        answer = chat_response.json()['choices'][0]['message']['content']
        return {"answer": answer.strip(), "sources": context_chunks}
    except Exception as e:
        logger.error(f"Chat failed: {repr(e)}"); return Response(status_code=500, content=f"Error: {repr(e)}")