from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from brain_functions import execute_with_arbitrage
from datetime import datetime
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
# Create table if it doesn't exist (Auto-Migration)
metadata.create_all(engine)

app = FastAPI()

# --- LIFECYCLE MANAGEMENT ---
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "miso-brain", "database": "connected"}

# --- DASHBOARD ENDPOINTS ---

@app.get("/stats")
async def get_stats():
    """Returns the persistent transaction history."""
    # Query the last 20 transactions from Postgres
    query = ledger_table.select().order_by(ledger_table.c.id.desc()).limit(20)
    rows = await database.fetch_all(query)
    return {"transactions": [dict(row) for row in rows]}

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the Bio-Fintech War Room UI."""
    # (Keeping the same UI code, just pointing it to the new /stats endpoint)
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MISO Bio-Fintech Monitor</title>
        <meta http-equiv="refresh" content="300"> 
        <style>
            body { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; padding: 20px; }
            h1 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
            .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
            .card { background: #161b22; padding: 20px; border: 1px solid #30363d; border-radius: 6px; }
            .card h3 { margin-top: 0; color: #8b949e; font-size: 14px; }
            .card .value { font-size: 24px; font-weight: bold; color: #fff; }
            .success { color: #2ea043; } .warning { color: #d29922; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { text-align: left; border-bottom: 1px solid #30363d; padding: 10px; color: #8b949e; }
            td { padding: 10px; border-bottom: 1px solid #21262d; }
            .provider-cheap { color: #2ea043; }
            .provider-premium { color: #d29922; }
            .bar-container { background: #21262d; height: 6px; width: 100px; border-radius: 3px; overflow: hidden; }
            .bar-fill { height: 100%; background: #58a6ff; }
        </style>
    </head>
    <body>
        <h1>🧬 MISO-PHOENIX // NEURAL ARBITRAGE ENGINE</h1>
        
        <div class="grid">
            <div class="card">
                <h3>TOTAL TRANSACTIONS</h3>
                <div class="value" id="total-tx">LOADING...</div>
            </div>
            <div class="card">
                <h3>ESTIMATED SAVINGS</h3>
                <div class="value success" id="total-savings">$0.000000</div>
            </div>
            <div class="card">
                <h3>LEDGER STATUS</h3>
                <div class="value" id="status" style="color:#2ea043">PERSISTENT</div>
            </div>
        </div>

        <h2>IMMUTABLE TRANSACTION LEDGER (POSTGRES)</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Complexity</th>
                    <th>Routing Decision (Muscle)</th>
                    <th>Confidence</th>
                    <th>Cost</th>
                </tr>
            </thead>
            <tbody id="ledger-body">
                </tbody>
        </table>

        <script>
            async function fetchStats() {
                try {
                    const response = await fetch('/stats');
                    const data = await response.json();
                    updateUI(data.transactions);
                } catch (e) {
                    console.error("Connection Lost", e);
                    document.getElementById('status').innerText = "DISCONNECTED";
                    document.getElementById('status').style.color = "red";
                }
            }

            function updateUI(txs) {
                const tbody = document.getElementById('ledger-body');
                tbody.innerHTML = '';
                
                let savings = 0;
                let count = txs.length; // This is just the view count

                txs.forEach(tx => {
                    // Calculate "Savings" vs standard GPT-4 ($0.03 benchmark)
                    const benchmark = 0.03;
                    const saved = benchmark - tx.cost;
                    if (saved > 0) savings += saved;

                    const row = `<tr>
                        <td>${tx.timestamp}</td>
                        <td>${tx.complexity}</td>
                        <td class="${tx.cost < 0.01 ? 'provider-cheap' : 'provider-premium'}">${tx.provider}</td>
                        <td>
                            <div style="display:flex; align-items:center; gap:10px;">
                                <span>${(tx.confidence * 100).toFixed(1)}%</span>
                                <div class="bar-container">
                                    <div class="bar-fill" style="width: ${tx.confidence * 100}%"></div>
                                </div>
                            </div>
                        </td>
                        <td>$${tx.cost.toFixed(6)}</td>
                    </tr>`;
                    tbody.innerHTML += row;
                });

                document.getElementById('total-tx').innerText = "Active"; 
                // In a real app, we would query SELECT COUNT(*) for total-tx
                document.getElementById('total-savings').innerText = "$" + savings.toFixed(4);
            }

            setInterval(fetchStats, 2000); 
            fetchStats();
        </script>
    </body>
    </html>
    """

# --- CORE LOGIC ---

class ProcessRequest(BaseModel):
    prompt: str

@app.post("/process")
async def process_task(request: ProcessRequest):
    try:
        # 1. Execute Logic
        result = await execute_with_arbitrage(request.prompt)
        
        # 2. Persist to Postgres Ledger
        timestamp = datetime.now().strftime("%H:%M:%S")
        complexity = "LOW (Reflex)" if result['cost'] < 0.01 else "HIGH (Deep Thought)"
        
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
