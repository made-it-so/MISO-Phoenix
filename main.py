from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from brain_functions import execute_with_arbitrage
from datetime import datetime
from typing import Optional
import os
import databases
import sqlalchemy

# --- DATABASE CONFIGURATION ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dbpassword@miso-db:5432/miso_db")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# The Ledger Schema
ledger_table = sqlalchemy.Table(
    "ledger",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("timestamp", sqlalchemy.String),
    sqlalchemy.Column("provider", sqlalchemy.String),
    sqlalchemy.Column("cost", sqlalchemy.Float),
    sqlalchemy.Column("confidence", sqlalchemy.Float),
    sqlalchemy.Column("complexity", sqlalchemy.String),
    sqlalchemy.Column("prompt_snippet", sqlalchemy.String),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "miso-brain", "database": "connected"}

@app.get("/stats")
async def get_stats():
    query = ledger_table.select().order_by(ledger_table.c.id.desc()).limit(20)
    rows = await database.fetch_all(query)
    return {"transactions": [dict(row) for row in rows]}

class ProcessRequest(BaseModel):
    prompt: str
    image: Optional[str] = None  # NEW: Accept Base64 Image

@app.post("/process")
async def process_task(request: ProcessRequest):
    try:
        # Pass both prompt AND image to the brain
        result = await execute_with_arbitrage(request.prompt, request.image)

        # Persist to Postgres
        timestamp = datetime.now().strftime("%H:%M:%S")
        complexity = "VISION" if request.image else ("LOW" if result['cost'] < 0.01 else "HIGH")

        query = ledger_table.insert().values(
            timestamp=timestamp,
            provider=result["provider"].upper(),
            cost=result["cost"],
            confidence=result["confidence"],
            complexity=complexity,
            prompt_snippet=request.prompt[:50]
        )
        await database.execute(query)

        return {
            "status": "success",
            "data": {
                "response": result["answer"],
                "meta": {
                    "confidence_score": result["confidence"],
                    "arbitrage_decision": result["logic"]
                },
                "audit_ledger": {
                    "cost": f"${result['cost']:.6f}",
                    "provider": result["provider"]
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
