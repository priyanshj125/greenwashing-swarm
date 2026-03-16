"""
FastAPI Application Entry Point — Greenwash Swarm Backend
"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root (one level above backend/)
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

# Ensure agents/ directory is on path when running from backend/
sys.path.insert(0, str(_project_root))

from backend.routers.analyze import router as analyze_router
from backend.routers.status import router as status_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed ChromaDB with ground truth benchmarks."""
    if DEMO_MODE:
        logger.info("🎭 DEMO MODE is ON — ML models will NOT be loaded")
    logger.info("🌿 Greenwash Swarm backend starting up...")

    if not DEMO_MODE:
        try:
            from backend.services.vector_store import seed_benchmarks
            added = seed_benchmarks()
            logger.info("ChromaDB seeded: %d documents added", added)
        except Exception as e:
            logger.warning("ChromaDB seed failed (non-fatal): %s", e)
    else:
        logger.info("Skipping ChromaDB seeding in demo mode")

    yield
    logger.info("Greenwash Swarm backend shutting down")


app = FastAPI(
    title="Greenwash Swarm API",
    description=(
        "5-agent LangGraph swarm for ESG greenwashing detection. "
        "Analyzes corporate ESG PDFs and social media feeds to calculate a Greenwash Integrity Score."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(status_router, prefix="/api", tags=["Status"])


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "greenwash-swarm"}


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Greenwash Swarm API",
        "docs": "/docs",
        "agents": ["harvester", "social_monitor", "auditor", "fact_checker", "judge"],
    }
