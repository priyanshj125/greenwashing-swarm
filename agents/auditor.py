"""
Agent B: Auditor
────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Score every claim for climate sentiment using ClimateBERT
  2. Classify each claim as Environmental/Social/Governance/Neutral via FinBERT-ESG
  3. Apply hyperbole heuristic: HIGH sentiment + ZERO numbers = HIGH RISK
  4. Detect PDF vs Social discrepancies (same topic, contradictory assertions)
"""
import re
import logging
from datetime import datetime
from typing import List, Optional
from difflib import SequenceMatcher

from agents.state import SwarmState, ClaimResult, AuditResult, TrailEntry

logger = logging.getLogger(__name__)

# ── Model loading with CPU fallback ──────────────────────────────────────────
_climate_pipeline = None
_finbert_pipeline = None


def _load_models():
    global _climate_pipeline, _finbert_pipeline
    if _climate_pipeline is not None:
        return  # already loaded

    try:
        from transformers import pipeline
        logger.info("🤖 Loading ClimateBERT (climatebert/distilroberta-base-climate-sentiment)...")
        _climate_pipeline = pipeline(
            "text-classification",
            model="climatebert/distilroberta-base-climate-sentiment",
            device=-1,   # CPU
            truncation=True,
            max_length=512,
        )
        logger.info("✅ ClimateBERT loaded")
    except Exception as e:
        logger.warning("ClimateBERT failed to load: %s — using keyword heuristic", e)
        _climate_pipeline = None

    try:
        from transformers import pipeline
        logger.info("🤖 Loading FinBERT-ESG (yiyanghkust/finbert-esg)...")
        _finbert_pipeline = pipeline(
            "text-classification",
            model="yiyanghkust/finbert-esg",
            device=-1,
            truncation=True,
            max_length=512,
        )
        logger.info("✅ FinBERT-ESG loaded")
    except Exception as e:
        logger.warning("FinBERT-ESG failed to load: %s — using keyword fallback", e)
        _finbert_pipeline = None


# ── Keyword fallbacks ─────────────────────────────────────────────────────────
POSITIVE_CLIMATE_WORDS = [
    "committed", "passionate", "proud", "leader", "pioneer", "transforming",
    "revolutionizing", "best", "world-class", "excellent", "outstanding",
    "milestone", "achieve", "officially", "100%", "neutral", "zero",
]

ESG_CATEGORY_KEYWORDS = {
    "Environmental": [
        "carbon", "emissions", "climate", "renewable", "energy", "water",
        "waste", "biodiversity", "nature", "pollution", "greenhouse",
    ],
    "Social": [
        "diversity", "inclusion", "human rights", "labor", "community",
        "health", "safety", "employees", "workers", "social",
    ],
    "Governance": [
        "board", "governance", "audit", "compliance", "ethics", "transparency",
        "accountability", "policy", "regulation",
    ],
}


def _climate_sentiment_score(text: str) -> float:
    """Returns a 0.0–1.0 positive climate sentiment score."""
    if _climate_pipeline:
        try:
            result = _climate_pipeline(text[:512])[0]
            # Model labels: "Positive", "Negative", "Neutral"
            if result["label"] == "Positive":
                return result["score"]
            elif result["label"] == "Negative":
                return 1.0 - result["score"]
            else:
                return 0.5
        except Exception as e:
            logger.debug("ClimateBERT inference error: %s", e)

    # Keyword fallback
    text_lower = text.lower()
    hits = sum(1 for w in POSITIVE_CLIMATE_WORDS if w in text_lower)
    return min(hits / 4.0, 1.0)


def _classify_esg_category(text: str) -> str:
    if _finbert_pipeline:
        try:
            result = _finbert_pipeline(text[:512])[0]
            return result["label"]   # Environmental | Social | Governance | None
        except Exception as e:
            logger.debug("FinBERT-ESG inference error: %s", e)

    # Keyword fallback
    text_lower = text.lower()
    scores = {}
    for category, keywords in ESG_CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Neutral"


def _has_numbers(text: str) -> bool:
    return bool(re.search(r'\d+(?:\.\d+)?(?:\s*%|[KMB]t?|\s*MW|\s*kg|\s*tons?)?', text))


def _assess_risk(sentiment: float, has_numbers: bool) -> tuple[str, str]:
    """Returns (risk_level, risk_reason)."""
    if sentiment > 0.80 and not has_numbers:
        return "HIGH", (
            f"Very high positive sentiment ({sentiment:.0%}) with zero numerical evidence. "
            "Classic greenwash pattern: aspirational language without measurable proof."
        )
    elif sentiment > 0.55 and not has_numbers:
        return "MEDIUM", (
            f"Elevated sentiment ({sentiment:.0%}) but no supporting figures. "
            "Claim is plausible but unverifiable."
        )
    elif has_numbers and sentiment > 0.70:
        return "LOW", (
            f"Contains numerical data — partially verifiable. Sentiment is positive ({sentiment:.0%})."
        )
    else:
        return "NEUTRAL", "Factual or low-sentiment claim — low greenwash risk."


CONTRADICTION_PAIRS = [
    # (pdf_signal, social_signal)
    (["exploring", "working toward", "aiming", "target", "aspire"], ["officially", "achieved", "100%", "neutral", "zero"]),
    (["reduced by", "decreased", "cut"], ["eliminated", "net zero", "carbon free"]),
    (["some", "partial", "certain"], ["all", "entire", "100%", "every"]),
]


def _detect_discrepancy(pdf_claim: ClaimResult, social_claim: ClaimResult) -> Optional[dict]:
    """
    Check if a PDF claim and a social claim are about the same topic
    but make contradictory assertions.
    """
    similarity = SequenceMatcher(None, pdf_claim["text"].lower(), social_claim["text"].lower()).ratio()
    if similarity < 0.10:   # unrelated topics
        return None

    pdf_lower = pdf_claim["text"].lower()
    social_lower = social_claim["text"].lower()

    for pdf_signals, social_signals in CONTRADICTION_PAIRS:
        pdf_match = any(sig in pdf_lower for sig in pdf_signals)
        social_match = any(sig in social_lower for sig in social_signals)
        if pdf_match and social_match:
            discrepancy_score = 0.5 + (similarity * 0.5)
            return {
                "pdf_claim": pdf_claim["text"],
                "social_claim": social_claim["text"],
                "discrepancy_score": round(discrepancy_score, 3),
                "topic_similarity": round(similarity, 3),
            }

    return None


def run_auditor(state: SwarmState) -> dict:
    """LangGraph node: Agent B — Auditor."""
    _load_models()

    trail: List[TrailEntry] = []
    start = datetime.utcnow().isoformat()
    trail.append(TrailEntry(
        agent="auditor",
        timestamp=start,
        action="start",
        detail=f"Auditing {len(state.get('claims', []))} claims",
        severity="info",
    ))

    all_claims: List[ClaimResult] = state.get("claims", [])
    pdf_claims = [c for c in all_claims if c["source"] == "pdf"]
    social_claims = [c for c in all_claims if c["source"] == "social"]

    audit_results: List[AuditResult] = []
    discrepancy_count = 0

    for claim in all_claims:
        sentiment = _climate_sentiment_score(claim["text"])
        category = _classify_esg_category(claim["text"])
        has_numbers = _has_numbers(claim["text"])
        risk_level, risk_reason = _assess_risk(sentiment, has_numbers)

        # Check for PDF↔Social discrepancies
        discrepancy_flag = False
        discrepancy_pair = None

        if claim["source"] == "pdf":
            for sc in social_claims:
                pair = _detect_discrepancy(claim, sc)
                if pair:
                    discrepancy_flag = True
                    discrepancy_pair = pair
                    discrepancy_count += 1
                    risk_level = "HIGH"
                    risk_reason = (
                        f"DISCREPANCY: PDF says '{claim['text'][:80]}...' but "
                        f"social media claims '{sc['text'][:80]}...'"
                    )
                    break

        audit_results.append(AuditResult(
            claim_id=claim["id"],
            text=claim["text"],
            source=claim["source"],
            climate_sentiment=round(sentiment, 4),
            esg_category=category,
            has_numbers=has_numbers,
            risk_level=risk_level,
            risk_reason=risk_reason,
            discrepancy_flag=discrepancy_flag,
            discrepancy_pair=discrepancy_pair,
        ))

        if risk_level == "HIGH":
            trail.append(TrailEntry(
                agent="auditor",
                timestamp=datetime.utcnow().isoformat(),
                action="flag",
                detail=f"🚩 HIGH RISK: {claim['text'][:100]}",
                severity="flag",
            ))

    high_count = sum(1 for a in audit_results if a["risk_level"] == "HIGH")
    trail.append(TrailEntry(
        agent="auditor",
        timestamp=datetime.utcnow().isoformat(),
        action="complete",
        detail=(
            f"Audited {len(audit_results)} claims | "
            f"HIGH: {high_count} | Discrepancies: {discrepancy_count}"
        ),
        severity="flag" if high_count > 0 else "info",
    ))

    return {
        "audit_results": audit_results,
        "reasoning_trail": trail,
        "status": "auditing_done",
    }
