import os
from flask import Flask, request, jsonify
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Configuration ---
app = Flask(__name__)
INDEX_NAME = "miso-meta-index"
# LangChain automatically uses these environment variables:
# OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# --- API Endpoints ---
@app.route("/")
def read_root():
    return jsonify(message="MISO Meta-Analysis Engine is Operational.")

@app.route("/ingest-log", methods=['POST'])
def ingest_log():
    try:
        if 'file' not in request.files: return jsonify(error="No file part"), 400
        file = request.files['file']
        if file.filename == '': return jsonify(error="No selected file"), 400

        temp_file_path = f"/tmp/{file.filename}"
        file.save(temp_file_path)

        loader = TextLoader(temp_file_path)
        documents = loader.load_and_split(text_splitter=text_splitter)
        PineconeVectorStore.from_documents(documents, embeddings, index_name=INDEX_NAME)

        os.remove(temp_file_path)

        return jsonify(status="success", filename=file.filename, documents_ingested=len(documents))
    except Exception as e:
        app.logger.error(f"Ingestion failed: {repr(e)}")
        return jsonify(error=str(e)), 500