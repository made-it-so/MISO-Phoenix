from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, Route Test"}

@app.post("/ingest-log")
def ingest_log(file: UploadFile = File(...)):
    return {"status": "success", "message": "Endpoint reached successfully", "filename": file.filename}
