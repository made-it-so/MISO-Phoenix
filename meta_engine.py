import os
from fastapi import FastAPI, UploadFile, File
from langchain_pinecone import PineconeVectorStore
from langchain_together import TogetherEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

# --- Configuration ---
app = FastAPI()
# LangChain automatically uses these environment variables
# PINECONE_API_KEY, PINECONE_ENVIRONMENT, TOGETHER_API_KEY
INDEX_NAME = "miso-meta-index"

# Initialize our high-level components from LangChain
embeddings = TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# --- API Endpoints ---
@app.get("/")
def read_root(): return {"message": "MISO Meta-Analysis Engine (LangChain) is Operational."}

@app.post("/ingest-log")
def ingest_log(file: UploadFile = File(...)):
    # Read the temp file
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    # Use LangChain to load and split the document
    from langchain.document_loaders import TextLoader
    loader = TextLoader(temp_file_path)
    documents = loader.load_and_split(text_splitter=text_splitter)
    
    # Use LangChain to create the Pinecone index from the documents and embeddings
    # This single command handles batching, embedding, and uploading.
    vectorstore = PineconeVectorStore.from_documents(documents, embeddings, index_name=INDEX_NAME)

    os.remove(temp_file_path) # Clean up the temp file
    
    return {"status": "success", "filename": file.filename, "documents_ingested": len(documents)}