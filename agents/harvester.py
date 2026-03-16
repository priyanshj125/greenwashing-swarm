"""
Agent A1: Harvester
────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Parse ESG PDF → extract raw text (with OCR fallback for image-heavy PDFs)
  2. Detect industry context → materiality tags
  3. Segment text into "Claims" (ESG-relevant sentences)
"""
import re
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# PDF parsing
try:
    from unstructured.partition.pdf import partition_pdf
    HAS_UNSTRUCTURED = True
except ImportError:
    HAS_UNSTRUCTURED = False

# OCR fallback
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from agents.state import SwarmState, ClaimResult, TrailEntry

logger = logging.getLogger(__name__)

# ── ESG keyword taxonomy ──────────────────────────────────────────────────────
ESG_KEYWORDS = {
    "carbon": ["carbon", "co2", "emissions", "scope 1", "scope 2", "scope 3", "ghg", "greenhouse"],
    "net_zero": ["net zero", "net-zero", "carbon neutral", "climate neutral", "carbon negative"],
    "renewable": ["renewable", "solar", "wind", "clean energy", "green energy", "sustainable energy"],
    "water": ["water", "wastewater", "freshwater", "water usage", "water stewardship"],
    "waste": ["waste", "circular economy", "recycling", "landfill", "zero waste"],
    "biodiversity": ["biodiversity", "nature", "ecosystems", "deforestation", "habitat"],
    "supply_chain": ["supply chain", "sourcing", "suppliers", "procurement", "raw material"],
    "social": ["diversity", "inclusion", "human rights", "labor", "community", "health and safety"],
    "governance": ["board", "governance", "transparency", "audit", "compliance", "ethics"],
}

# ── Industry materiality weights ──────────────────────────────────────────────
INDUSTRY_KEYWORDS = {
    "energy": ["oil", "gas", "petroleum", "refinery", "pipeline", "energy company"],
    "mining": ["mining", "extraction", "minerals", "coal", "metals"],
    "finance": ["bank", "investment", "portfolio", "asset management", "insurance"],
    "retail": ["retail", "consumer goods", "fashion", "apparel", "supply chain"],
    "tech": ["technology", "software", "data center", "cloud", "semiconductor"],
}

MATERIALITY_WEIGHTS = {
    "energy": {"carbon": 0.9, "net_zero": 0.9, "renewable": 0.8, "water": 0.4},
    "mining": {"carbon": 0.7, "water": 0.9, "biodiversity": 0.9, "waste": 0.7},
    "finance": {"governance": 0.9, "supply_chain": 0.7, "social": 0.8},
    "retail": {"supply_chain": 0.9, "waste": 0.8, "social": 0.8},
    "tech": {"carbon": 0.7, "social": 0.8, "governance": 0.7, "water": 0.5},
    "general": {k: 0.5 for k in ESG_KEYWORDS},
}


def _detect_industry(text: str) -> str:
    text_lower = text.lower()
    for industry, kws in INDUSTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            return industry
    return "general"


def _tag_materiality(sentence: str) -> str:
    sentence_lower = sentence.lower()
    for tag, kws in ESG_KEYWORDS.items():
        if any(kw in sentence_lower for kw in kws):
            return tag
    return "general"


def _is_esg_relevant(sentence: str) -> bool:
    sentence_lower = sentence.lower()
    return any(
        kw in sentence_lower
        for kws in ESG_KEYWORDS.values()
        for kw in kws
    )


def _has_numbers(text: str) -> bool:
    return bool(re.search(r'\d+(?:\.\d+)?(?:\s*%|[KMB]|\s*tons?|\s*MW|\s*kg)?', text))


def _extract_text_unstructured(pdf_path: str) -> tuple[str, str]:
    """Primary extraction via unstructured library."""
    elements = partition_pdf(filename=pdf_path, strategy="fast")
    text = "\n".join(str(el) for el in elements if str(el).strip())
    return text, "unstructured"


def _extract_text_ocr(pdf_path: str) -> tuple[str, str]:
    """OCR fallback for image-heavy/scanned PDFs."""
    logger.info("🔍 OCR fallback activated for %s", pdf_path)
    images = convert_from_path(pdf_path, dpi=200)
    pages = []
    for i, img in enumerate(images):
        try:
            page_text = pytesseract.image_to_string(img, lang="eng")
            pages.append(page_text)
        except Exception as e:
            logger.warning("OCR failed on page %d: %s", i + 1, e)
    return "\n".join(pages), "ocr"


def _extract_text(pdf_path: str) -> tuple[str, str]:
    """Extract text with automatic OCR fallback."""
    # Try unstructured first
    if HAS_UNSTRUCTURED:
        try:
            text, method = _extract_text_unstructured(pdf_path)
            if len(text.strip()) > 200:   # reasonable amount of text
                return text, method
            logger.info("Unstructured returned thin text (%d chars) — trying OCR", len(text))
        except Exception as e:
            logger.warning("Unstructured failed: %s", e)

    # OCR fallback
    if HAS_OCR:
        try:
            return _extract_text_ocr(pdf_path)
        except Exception as e:
            logger.error("OCR also failed: %s", e)

    raise RuntimeError("Could not extract text from PDF — no working extractor available")


def _segment_claims(text: str, source_label: str = "pdf") -> List[ClaimResult]:
    """Split text into sentences and filter to ESG-relevant claims."""
    # Simple sentence splitter (avoids NLTK download requirement at runtime)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        if not _is_esg_relevant(sentence):
            continue
        claims.append(ClaimResult(
            id=str(uuid.uuid4()),
            text=sentence,
            page=0,       # page tracking requires element-level parsing
            source=source_label,
            esg_category="pending",   # filled by Auditor
            has_numbers=_has_numbers(sentence),
            materiality_tag=_tag_materiality(sentence),
        ))
    return claims


def run_harvester(state: SwarmState) -> dict:
    """
    LangGraph node: Agent A1 — Harvester
    Extracts claims from the PDF file at state["pdf_path"].
    Returns partial state update.
    """
    trail: List[TrailEntry] = []
    start = datetime.utcnow().isoformat()

    trail.append(TrailEntry(
        agent="harvester",
        timestamp=start,
        action="start",
        detail=f"Processing PDF: {state['pdf_path']}",
        severity="info",
    ))

    try:
        text, method = _extract_text(state["pdf_path"])
        industry = _detect_industry(text)
        claims = _segment_claims(text, source_label="pdf")

        trail.append(TrailEntry(
            agent="harvester",
            timestamp=datetime.utcnow().isoformat(),
            action="extracted",
            detail=(
                f"Method: {method} | Industry: {industry} | "
                f"Text chars: {len(text)} | ESG claims found: {len(claims)}"
            ),
            severity="info",
        ))

        return {
            "raw_text": text,
            "claims": claims,
            "reasoning_trail": trail,
            "status": "harvesting_done",
        }

    except Exception as exc:
        trail.append(TrailEntry(
            agent="harvester",
            timestamp=datetime.utcnow().isoformat(),
            action="error",
            detail=str(exc),
            severity="warning",
        ))
        return {
            "raw_text": "",
            "claims": [],
            "reasoning_trail": trail,
            "error": f"Harvester error: {exc}",
            "status": "error",
        }
