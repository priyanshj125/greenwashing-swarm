"""
FastAPI Router: GET /api/status/{job_id}
Server-Sent Events stream — pushes real-time agent status updates to the frontend.
"""
import asyncio
import json
import logging
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from backend.routers.analyze import JOB_STORE

router = APIRouter()
logger = logging.getLogger(__name__)


async def _status_generator(job_id: str):
    """Yields SSE events until job is done or error."""
    last_trail_len = 0

    while True:
        if job_id not in JOB_STORE:
            yield {"event": "error", "data": json.dumps({"detail": "Job not found"})}
            break

        job = JOB_STORE[job_id]
        status = job["status"]
        result = job.get("result")

        # Push new trail entries if available
        if result:
            trail = result.get("reasoning_trail", [])
            new_entries = trail[last_trail_len:]
            for entry in new_entries:
                yield {
                    "event": "trail",
                    "data": json.dumps({
                        "agent": entry["agent"],
                        "action": entry["action"],
                        "detail": entry["detail"],
                        "severity": entry["severity"],
                        "timestamp": entry["timestamp"],
                    }),
                }
            last_trail_len = len(trail)

        # Push overall status
        yield {
            "event": "status",
            "data": json.dumps({"job_id": job_id, "status": status}),
        }

        if status in ("done", "error"):
            break

        await asyncio.sleep(1.5)


@router.get("/status/{job_id}")
async def stream_status(job_id: str):
    """SSE endpoint — streams reasoning trail + status updates."""
    return EventSourceResponse(_status_generator(job_id))
