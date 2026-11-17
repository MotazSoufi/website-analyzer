from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main_agent import analyze_website
import uuid
import threading
from database import setup_database, save_report, find_cached_report, list_history, get_report

app = FastAPI()
setup_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str
    refresh: bool = False

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

    if not request.refresh:
        cached = find_cached_report(url)
        if cached:
            job_id = uuid.uuid4().hex
            jobs[job_id] = {
                "steps": ["Found a saved report from the last 7 days."],
                "done": True,
                "report": cached,
                "error": None,
            }
            return {"job_id": job_id}

    job_id = uuid.uuid4().hex
    jobs[job_id] = {"steps": [], "done": False, "report": None, "error": None}

    def on_progress(message):
        jobs[job_id]["steps"].append(message)

    def worker():
        try:
            report = analyze_website(url, on_progress)
            if not report.get("failed_agents"):
                report["history_id"] = save_report(url, report)
            jobs[job_id]["report"] = report

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

@app.get("/history")
def history():
    """Short list of saved reports, newest first."""
    return list_history()

@app.get("/history/{report_id}")
def history_item(report_id: int):
    """One full saved report."""
    report = get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report     