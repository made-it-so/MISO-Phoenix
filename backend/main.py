from fastapi import FastAPI, BackgroundTasks
import subprocess
import os

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "MISO is online", "level": 5}

def run_git_pull():
    """Executes the git pull command safely in the background."""
    print(">> 🔄 API TRIGGER: Pulling latest code...")
    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print(">> ✅ GIT SUCCESS:", result.stdout)
    else:
        print(">> ❌ GIT ERROR:", result.stderr)

@app.post("/miso/trigger")
async def trigger_update(background_tasks: BackgroundTasks):
    """
    Endpoint called by GitHub Actions.
    Triggers a background git pull so the request returns immediately.
    """
    background_tasks.add_task(run_git_pull)
    return {"message": "Update triggered", "status": "processing"}
