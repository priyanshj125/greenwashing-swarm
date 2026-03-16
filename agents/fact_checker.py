"""
Agent C: Fact-Checker
────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Query ChromaDB (RAG) with each HIGH/MEDIUM risk audit result
  2. If RAG similarity < threshold → escalate to Tavily live web search
  3. Return verification status: verified | partial | unverified
"""
import logging
import os
from datetime import datetime
from typing import List

from agents.state import SwarmState, AuditResult, FactResult, TrailEntry

logger = logging.getLogger(__name__)

RAG_SIMILARITY_THRESHOLD = 0.60
VERIFY_RISK_LEVELS = {"HIGH", "MEDIUM"}


def _get_vector_store():
    """Lazy-load ChromaDB collection."""
    try:
        import chromadb
        from chromadb.config import Settings

        chroma_dir = os.getenv("CHROMA_DIR", "data/chroma_db")
        client = chromadb.PersistentClient(path=chroma_dir)
        collection = client.get_or_create_collection(
            name="esg_benchmarks",
            metadata={"hnsw:space": "cosine"},
        )
        return collection
    except Exception as e:
        logger.error("ChromaDB unavailable: %s", e)
        return None


def _get_embedder():
    """Lazy-load sentence-transformer embedder."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model
    except Exception as e:
        logger.warning("Embedder unavailable: %s", e)
        return None


_collection = None
_embedder = None


def _rag_verify(claim_text: str) -> dict:
    """Query ChromaDB for the most similar benchmark document."""
    global _collection, _embedder

    if _collection is None:
        _collection = _get_vector_store()
    if _embedder is None:
        _embedder = _get_embedder()

    if not _collection or not _embedder:
        return {"alignment_score": 0.0, "snippet": "", "source_url": "", "method": "none"}

    try:
        query_embedding = _embedder.encode([claim_text])[0].tolist()
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            return {"alignment_score": 0.0, "snippet": "", "source_url": "", "method": "none"}

        # Convert cosine distance → similarity
        best_distance = results["distances"][0][0]
        alignment = max(0.0, 1.0 - best_distance)

        best_doc = results["documents"][0][0]
        best_meta = results["metadatas"][0][0] if results["metadatas"][0] else {}

        return {
            "alignment_score": round(alignment, 4),
            "snippet": best_doc[:300],
            "source_url": best_meta.get("source_url", "ChromaDB local benchmark"),
            "method": "rag",
        }
    except Exception as e:
        logger.error("RAG query error: %s", e)
        return {"alignment_score": 0.0, "snippet": "", "source_url": "", "method": "none"}


def _tavily_verify(claim_text: str) -> dict:
    """Live web search via Tavily as escalation fallback."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"alignment_score": 0.0, "snippet": "Tavily API key not configured", "source_url": "", "method": "none"}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        query = f"ESG sustainability data evidence: {claim_text[:200]}"
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )

        answer = response.get("answer", "")
        results = response.get("results", [])
        top_result = results[0] if results else {}

        # Heuristic: if Tavily answer contradicts the claim, score is low
        claim_lower = claim_text.lower()
        answer_lower = answer.lower()

        contradiction_words = ["false", "misleading", "not", "didn't", "failed", "controversy"]
        contradiction_score = sum(1 for w in contradiction_words if w in answer_lower)
        alignment = max(0.1, 0.8 - contradiction_score * 0.15)

        return {
            "alignment_score": round(alignment, 4),
            "snippet": (answer or top_result.get("content", ""))[:400],
            "source_url": top_result.get("url", ""),
            "method": "web",
        }
    except Exception as e:
        logger.error("Tavily search error: %s", e)
        return {"alignment_score": 0.0, "snippet": str(e), "source_url": "", "method": "none"}


def _determine_status(alignment: float, method: str) -> str:
    if method == "none":
        return "unverified"
    if alignment >= 0.70:
        return "verified"
    if alignment >= 0.40:
        return "partial"
    return "unverified"


def run_fact_checker(state: SwarmState) -> dict:
    """LangGraph node: Agent C — Fact-Checker."""
    trail: List[TrailEntry] = []
    start = datetime.utcnow().isoformat()

    audit_results: List[AuditResult] = state.get("audit_results", [])
    to_check = [a for a in audit_results if a["risk_level"] in VERIFY_RISK_LEVELS]

    trail.append(TrailEntry(
        agent="fact_checker",
        timestamp=start,
        action="start",
        detail=f"Verifying {len(to_check)} HIGH/MEDIUM risk claims ({len(audit_results)} total)",
        severity="info",
    ))

    fact_results: List[FactResult] = []

    for audit in audit_results:
        if audit["risk_level"] not in VERIFY_RISK_LEVELS:
            # LOW/NEUTRAL claims: skip deep verification
            fact_results.append(FactResult(
                claim_id=audit["claim_id"],
                text=audit["text"],
                verification_status="verified",
                alignment_score=0.9,
                method="skipped",
                source_snippet="Low/neutral risk — verification skipped",
                source_url="",
            ))
            continue

        # Step 1: RAG
        rag_result = _rag_verify(audit["text"])
        method = rag_result["method"]
        alignment = rag_result["alignment_score"]
        snippet = rag_result["snippet"]
        source_url = rag_result["source_url"]

        # Step 2: Escalate to Tavily if RAG confidence is too low
        if alignment < RAG_SIMILARITY_THRESHOLD:
            logger.info("RAG score %.2f < threshold — escalating to Tavily", alignment)
            tavily_result = _tavily_verify(audit["text"])
            # Use whichever gives more confidence
            if tavily_result["alignment_score"] > alignment:
                alignment = tavily_result["alignment_score"]
                snippet = tavily_result["snippet"]
                source_url = tavily_result["source_url"]
                method = tavily_result["method"]

        status = _determine_status(alignment, method)

        fact_results.append(FactResult(
            claim_id=audit["claim_id"],
            text=audit["text"],
            verification_status=status,
            alignment_score=alignment,
            method=method,
            source_snippet=snippet,
            source_url=source_url,
        ))

        if status == "unverified":
            trail.append(TrailEntry(
                agent="fact_checker",
                timestamp=datetime.utcnow().isoformat(),
                action="unverified",
                detail=f"❌ Cannot verify: '{audit['text'][:80]}...' (alignment: {alignment:.0%})",
                severity="flag",
            ))

    verified_count = sum(1 for f in fact_results if f["verification_status"] == "verified")
    unverified_count = sum(1 for f in fact_results if f["verification_status"] == "unverified")

    trail.append(TrailEntry(
        agent="fact_checker",
        timestamp=datetime.utcnow().isoformat(),
        action="complete",
        detail=f"Verified: {verified_count} | Partial: {len(fact_results)-verified_count-unverified_count} | Unverified: {unverified_count}",
        severity="flag" if unverified_count > 0 else "info",
    ))

    return {
        "fact_results": fact_results,
        "reasoning_trail": trail,
        "status": "fact_checking_done",
    }
