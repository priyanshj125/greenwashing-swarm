"""
Agent D: Judge
────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Merge Auditor + Fact-Checker outputs
  2. Apply conflict resolution (e.g., Auditor says HIGH but Fact-Checker verifies → downgrade)
  3. Calculate final Greenwash Index (0–100) with documented formula
  4. Produce the FinalReport with Reasoning Trail summary
"""
import logging
from datetime import datetime
from typing import List

from agents.state import SwarmState, AuditResult, FactResult, FinalReport, TrailEntry

logger = logging.getLogger(__name__)

# ── Scoring weights ───────────────────────────────────────────────────────────
WEIGHT_AUDIT_RISK = 0.40
WEIGHT_FACT_DIVERGENCE = 0.40
WEIGHT_VAGUENESS = 0.20

RISK_SCORES = {"HIGH": 1.0, "MEDIUM": 0.55, "LOW": 0.15, "NEUTRAL": 0.0}
VERIFY_SCORES = {"unverified": 1.0, "partial": 0.50, "verified": 0.0, "skipped": 0.0}


def _conflict_resolution(
    audit: AuditResult,
    fact: FactResult,
) -> tuple[str, str]:
    """
    Downgrade Auditor risk if Fact-Checker confirms the claim.
    Return (resolved_risk, resolution_note).
    """
    original_risk = audit["risk_level"]

    if original_risk == "HIGH" and fact["verification_status"] == "verified":
        return "MEDIUM", (
            f"Downgraded HIGH→MEDIUM: Auditor flagged hyperbolic language but "
            f"Fact-Checker confirmed against benchmark (alignment: {fact['alignment_score']:.0%})"
        )
    if original_risk == "MEDIUM" and fact["verification_status"] == "verified":
        return "LOW", (
            f"Downgraded MEDIUM→LOW: Claim partially hyperbolic but benchmark-verified "
            f"(alignment: {fact['alignment_score']:.0%})"
        )
    if original_risk == "LOW" and fact["verification_status"] == "unverified":
        return "MEDIUM", (
            "Upgraded LOW→MEDIUM: Numerical claim present but no benchmark match found."
        )
    return original_risk, "No conflict resolution needed."


def _vagueness_score(text: str) -> float:
    """Penalize vague, non-committal language."""
    vague_words = [
        "aim", "aspire", "explore", "consider", "working toward",
        "hope to", "plan to", "intend to", "committed to",
        "strive", "endeavor", "seek to",
    ]
    text_lower = text.lower()
    hits = sum(1 for w in vague_words if w in text_lower)
    return min(hits / 3.0, 1.0)


def run_judge(state: SwarmState) -> dict:
    """LangGraph node: Agent D — Judge."""
    trail: List[TrailEntry] = []
    start = datetime.utcnow().isoformat()

    audit_results: List[AuditResult] = state.get("audit_results", [])
    fact_results: List[FactResult] = state.get("fact_results", [])

    trail.append(TrailEntry(
        agent="judge",
        timestamp=start,
        action="start",
        detail=f"Judging {len(audit_results)} audit results against {len(fact_results)} fact-check results",
        severity="info",
    ))

    # Build fact lookup
    fact_by_claim = {f["claim_id"]: f for f in fact_results}

    per_claim_indices = []
    for audit in audit_results:
        fact = fact_by_claim.get(audit["claim_id"])
        if not fact:
            fact = FactResult(
                claim_id=audit["claim_id"],
                text=audit["text"],
                verification_status="unverified",
                alignment_score=0.0,
                method="none",
                source_snippet="",
                source_url="",
            )

        # Conflict resolution
        resolved_risk, resolution_note = _conflict_resolution(audit, fact)

        # Component scores
        audit_score = RISK_SCORES.get(resolved_risk, 0.0)
        fact_score = VERIFY_SCORES.get(fact["verification_status"], 0.0)
        vagueness = _vagueness_score(audit["text"])
        discrepancy_bonus = 0.2 if audit.get("discrepancy_flag") else 0.0

        claim_index = (
            audit_score * WEIGHT_AUDIT_RISK
            + fact_score * WEIGHT_FACT_DIVERGENCE
            + vagueness * WEIGHT_VAGUENESS
            + discrepancy_bonus
        )
        claim_index = min(claim_index, 1.0)
        per_claim_indices.append(claim_index)

        if resolution_note != "No conflict resolution needed.":
            trail.append(TrailEntry(
                agent="judge",
                timestamp=datetime.utcnow().isoformat(),
                action="conflict_resolved",
                detail=resolution_note,
                severity="info",
            ))

    # Overall Greenwash Index (0–100)
    if per_claim_indices:
        raw_index = sum(per_claim_indices) / len(per_claim_indices)
        greenwash_index = round(raw_index * 100, 1)
    else:
        greenwash_index = 0.0

    # Risk band
    if greenwash_index >= 70:
        risk_band = "CRITICAL"
    elif greenwash_index >= 45:
        risk_band = "HIGH"
    elif greenwash_index >= 20:
        risk_band = "MEDIUM"
    else:
        risk_band = "LOW"

    # Counts
    high_count = sum(1 for a in audit_results if a["risk_level"] == "HIGH")
    med_count = sum(1 for a in audit_results if a["risk_level"] == "MEDIUM")
    low_count = sum(1 for a in audit_results if a["risk_level"] in ("LOW", "NEUTRAL"))
    verified_count = sum(1 for f in fact_results if f["verification_status"] == "verified")
    discrepancy_count = sum(1 for a in audit_results if a.get("discrepancy_flag"))

    summary = (
        f"Greenwash Index: {greenwash_index}/100 ({risk_band}). "
        f"Analysed {len(audit_results)} ESG claims. "
        f"{high_count} flagged HIGH risk, {discrepancy_count} PDF↔Social discrepancies found. "
        f"{verified_count} claims externally verified."
    )

    trail.append(TrailEntry(
        agent="judge",
        timestamp=datetime.utcnow().isoformat(),
        action="verdict",
        detail=f"⚖️ FINAL VERDICT: Greenwash Index = {greenwash_index}/100 | Band: {risk_band}",
        severity="flag" if greenwash_index >= 45 else "info",
    ))

    final_report = FinalReport(
        greenwash_index=greenwash_index,
        risk_band=risk_band,
        total_claims=len(audit_results),
        high_risk_count=high_count,
        medium_risk_count=med_count,
        low_risk_count=low_count,
        verified_count=verified_count,
        discrepancy_count=discrepancy_count,
        summary=summary,
    )

    return {
        "final_report": final_report,
        "reasoning_trail": trail,
        "status": "done",
    }
