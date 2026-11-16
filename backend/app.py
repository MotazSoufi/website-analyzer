from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main_agent import analyze_website
import uuid
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    url = request.url.strip()

    # this turns "nike.com" to "https://nike.com"
    if not url.startswith("http"):
        url = "https://" + url

    try:
        return analyze_website(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not analyze website: {e}")

jobs = {}

@app.post("/jobs")
def start_job(request: AnalyzeRequest):
    """Start an analysis in the background and return its ID right away."""
    url = request.url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    job_id = uuid.uuid4().hex
    jobs[job_id] = {"steps": [], "done": False, "report": None, "error": None}

    def on_progress(message):
        jobs[job_id]["steps"].append(message)

    def worker():
        try:
            jobs[job_id]["report"] = analyze_website(url, on_progress)
        except Exception as e:
            jobs[job_id]["error"] = f"Could not analyze website: {e}"
        finally:
            jobs[job_id]["done"] = True

    threading.Thread(target=worker, daemon=True).start()
    return {"job_id": job_id}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Return the progress (and the report, once done) of a job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job       