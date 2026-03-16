"""
FastAPI Router: POST /api/analyze
Accepts PDF + optional company_url, launches swarm as background task.
"""
import os
import uuid
import logging
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from backend.models.schemas import AnalysisResponse, AnalyzeRequest
from agents.state import SwarmState

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory job store (replace with Redis in production)
JOB_STORE: dict[str, dict] = {}
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/uploads"))


async def _run_swarm_job(job_id: str, pdf_path: str, company_url: str | None):
    """Background task: runs the full LangGraph swarm (or demo swarm) and stores result."""
    demo_mode = os.getenv("DEMO_MODE", "").lower() == "true"

    JOB_STORE[job_id]["status"] = "running"
    JOB_STORE[job_id]["started_at"] = datetime.utcnow().isoformat()
    # Initialize partial result for SSE trail streaming
    JOB_STORE[job_id]["result"] = {"reasoning_trail": []}

    try:
        if demo_mode:
            from backend.services.demo_swarm import run_demo_swarm
            logger.info("🎭 DEMO MODE — using mock swarm for job %s", job_id)

            def on_trail(entry):
                JOB_STORE[job_id]["result"]["reasoning_trail"].append(entry)

            final_state = await run_demo_swarm(job_id, pdf_path, company_url, on_trail=on_trail)
        else:
            from agents.supervisor import get_swarm

            initial_state = SwarmState(
                pdf_path=pdf_path,
                company_url=company_url,
                job_id=job_id,
                raw_text="",
                social_posts=[],
                claims=[],
                screenshots=[],
                audit_results=[],
                fact_results=[],
                final_report=None,
                reasoning_trail=[],
                error=None,
                status="queued",
            )

            swarm = get_swarm()
            final_state = await swarm.ainvoke(initial_state)

        JOB_STORE[job_id]["result"] = final_state
        JOB_STORE[job_id]["status"] = "done"
    except Exception as e:
        logger.exception("Swarm job %s failed", job_id)
        JOB_STORE[job_id]["status"] = "error"
        JOB_STORE[job_id]["error"] = str(e)


@router.post("/analyze", response_model=dict)
async def analyze_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_url: str | None = Form(None),
):
    """Upload an ESG PDF + optional social URL to start a Greenwash Swarm analysis."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    job_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{job_id}_{file.filename}"

    # Save PDF
    content = await file.read()
    pdf_path.write_bytes(content)
    logger.info("PDF saved: %s (%d bytes)", pdf_path, len(content))

    # Register job
    JOB_STORE[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "pdf_path": str(pdf_path),
        "company_url": company_url,
        "created_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(_run_swarm_job, job_id, str(pdf_path), company_url)

    return {"job_id": job_id, "status": "queued", "message": "Swarm analysis started"}


@router.get("/result/{job_id}", response_model=AnalysisResponse)
async def get_result(job_id: str):
    """Poll for the completed analysis result."""
    if job_id not in JOB_STORE:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOB_STORE[job_id]

    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Unknown error"))

    if job["status"] != "done":
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": job["status"]},
        )

    state = job["result"]
    return AnalysisResponse(
        job_id=job_id,
        status="done",
        final_report=state.get("final_report"),
        audit_results=state.get("audit_results", []),
        fact_results=state.get("fact_results", []),
        reasoning_trail=state.get("reasoning_trail", []),
        social_posts=state.get("social_posts", []),
        screenshots=state.get("screenshots", []),
    )
