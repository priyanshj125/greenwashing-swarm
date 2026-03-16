"""
Demo Swarm — Returns realistic mock analysis data.
Used when DEMO_MODE=true to bypass heavy ML dependencies.
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── Realistic mock claims ────────────────────────────────────────────────────

DEMO_CLAIMS = [
    {
        "id": "claim-001",
        "text": "We have achieved 100% carbon neutrality across all global operations since 2023.",
        "page": 3,
        "source": "pdf",
        "esg_category": "Environmental",
        "has_numbers": False,
        "materiality_tag": "carbon",
    },
    {
        "id": "claim-002",
        "text": "Our renewable energy procurement has increased by 45% year-over-year, exceeding industry benchmarks.",
        "page": 7,
        "source": "pdf",
        "esg_category": "Environmental",
        "has_numbers": True,
        "materiality_tag": "renewable",
    },
    {
        "id": "claim-003",
        "text": "We are committed to achieving net-zero emissions by 2030, well ahead of the Paris Agreement timeline.",
        "page": 4,
        "source": "pdf",
        "esg_category": "Environmental",
        "has_numbers": False,
        "materiality_tag": "carbon",
    },
    {
        "id": "claim-004",
        "text": "100% of our supply chain partners have undergone ethical sourcing audits in 2024.",
        "page": 12,
        "source": "pdf",
        "esg_category": "Social",
        "has_numbers": True,
        "materiality_tag": "supply_chain",
    },
    {
        "id": "claim-005",
        "text": "Our water recycling program has saved 2.3 billion liters since inception, making us water-positive.",
        "page": 9,
        "source": "pdf",
        "esg_category": "Environmental",
        "has_numbers": True,
        "materiality_tag": "water",
    },
    {
        "id": "claim-006",
        "text": "We have reduced Scope 1 and Scope 2 emissions by 62% compared to our 2019 baseline.",
        "page": 5,
        "source": "pdf",
        "esg_category": "Environmental",
        "has_numbers": True,
        "materiality_tag": "carbon",
    },
    {
        "id": "claim-007",
        "text": "Our ESG governance framework is best-in-class and exceeds all regulatory requirements globally.",
        "page": 15,
        "source": "pdf",
        "esg_category": "Governance",
        "has_numbers": False,
        "materiality_tag": "governance",
    },
    {
        "id": "claim-008",
        "text": "We have planted 10 million trees as part of our reforestation initiative to offset remaining emissions.",
        "page": 11,
        "source": "pdf",
        "esg_category": "Environmental",
        "has_numbers": True,
        "materiality_tag": "carbon",
    },
]

DEMO_SOCIAL_POSTS = [
    {
        "text": "Thrilled to announce our journey to carbon neutrality! 🌍 Our team has worked tirelessly to make sustainability our core mission. #GreenFuture #ESG",
        "date": "2024-11-15",
        "url": "https://linkedin.com/posts/acme-corp/carbon-neutral",
        "platform": "LinkedIn",
        "screenshot_path": None,
        "sentiment_keywords": ["thrilled", "sustainability", "core mission", "green future"],
    },
    {
        "text": "Proud that our new factory in Gujarat is already running on 100% renewable energy! The future is green. ☀️⚡",
        "date": "2024-10-22",
        "url": "https://linkedin.com/posts/acme-corp/renewable-factory",
        "platform": "LinkedIn",
        "screenshot_path": None,
        "sentiment_keywords": ["proud", "100% renewable", "future is green"],
    },
    {
        "text": "Our CEO says: 'We don't just follow ESG standards — we set them.' Read our latest sustainability report for the full story.",
        "date": "2024-12-01",
        "url": "https://linkedin.com/posts/acme-corp/ceo-statement",
        "platform": "LinkedIn",
        "screenshot_path": None,
        "sentiment_keywords": ["set standards", "sustainability", "full story"],
    },
]

DEMO_AUDIT_RESULTS = [
    {
        "claim_id": "claim-001",
        "text": DEMO_CLAIMS[0]["text"],
        "source": "pdf",
        "climate_sentiment": 0.92,
        "esg_category": "Environmental",
        "has_numbers": False,
        "risk_level": "HIGH",
        "risk_reason": "Vague 'carbon neutrality' claim with high sentiment (0.92) but NO quantified data. No mention of Scope 3 emissions or verification methodology.",
        "discrepancy_flag": True,
        "discrepancy_pair": {
            "pdf_claim": "We have achieved 100% carbon neutrality across all global operations since 2023.",
            "social_claim": "Thrilled to announce our journey to carbon neutrality! Our team has worked tirelessly...",
            "discrepancy_score": 0.78,
        },
    },
    {
        "claim_id": "claim-002",
        "text": DEMO_CLAIMS[1]["text"],
        "source": "pdf",
        "climate_sentiment": 0.65,
        "esg_category": "Environmental",
        "has_numbers": True,
        "risk_level": "LOW",
        "risk_reason": "Specific quantified claim (45% increase) with industry benchmark reference. Lower greenwash risk due to measurability.",
        "discrepancy_flag": False,
        "discrepancy_pair": None,
    },
    {
        "claim_id": "claim-003",
        "text": DEMO_CLAIMS[2]["text"],
        "source": "pdf",
        "climate_sentiment": 0.88,
        "esg_category": "Environmental",
        "has_numbers": False,
        "risk_level": "HIGH",
        "risk_reason": "Net-zero by 2030 claim lacks interim milestones. High sentiment language without roadmap. Paris Agreement reference is misleading — corporates are not bound.",
        "discrepancy_flag": False,
        "discrepancy_pair": None,
    },
    {
        "claim_id": "claim-004",
        "text": DEMO_CLAIMS[3]["text"],
        "source": "pdf",
        "climate_sentiment": 0.58,
        "esg_category": "Social",
        "has_numbers": True,
        "risk_level": "MEDIUM",
        "risk_reason": "100% audit claim is bold. CDP data shows <5% of companies achieve full supply chain audits. Requires independent audit verification.",
        "discrepancy_flag": False,
        "discrepancy_pair": None,
    },
    {
        "claim_id": "claim-005",
        "text": DEMO_CLAIMS[4]["text"],
        "source": "pdf",
        "climate_sentiment": 0.72,
        "esg_category": "Environmental",
        "has_numbers": True,
        "risk_level": "MEDIUM",
        "risk_reason": "'Water-positive' claim requires AWS Standard site-level verification. 2.3B liters is specific but lacks watershed baseline context.",
        "discrepancy_flag": True,
        "discrepancy_pair": {
            "pdf_claim": "Our water recycling program has saved 2.3 billion liters since inception, making us water-positive.",
            "social_claim": "Proud that our new factory in Gujarat is already running on 100% renewable energy!",
            "discrepancy_score": 0.45,
        },
    },
    {
        "claim_id": "claim-006",
        "text": DEMO_CLAIMS[5]["text"],
        "source": "pdf",
        "climate_sentiment": 0.55,
        "esg_category": "Environmental",
        "has_numbers": True,
        "risk_level": "LOW",
        "risk_reason": "Quantified reduction with baseline year. 62% exceeds CDP avg (3.1%/yr) — high but verifiable if audited.",
        "discrepancy_flag": False,
        "discrepancy_pair": None,
    },
    {
        "claim_id": "claim-007",
        "text": DEMO_CLAIMS[6]["text"],
        "source": "pdf",
        "climate_sentiment": 0.85,
        "esg_category": "Governance",
        "has_numbers": False,
        "risk_level": "HIGH",
        "risk_reason": "'Best-in-class' and 'exceeds all regulatory requirements' are superlative claims with no supporting evidence or external ranking citation.",
        "discrepancy_flag": True,
        "discrepancy_pair": {
            "pdf_claim": "Our ESG governance framework is best-in-class and exceeds all regulatory requirements globally.",
            "social_claim": "Our CEO says: 'We don't just follow ESG standards — we set them.'",
            "discrepancy_score": 0.65,
        },
    },
    {
        "claim_id": "claim-008",
        "text": DEMO_CLAIMS[7]["text"],
        "source": "pdf",
        "climate_sentiment": 0.62,
        "esg_category": "Environmental",
        "has_numbers": True,
        "risk_level": "MEDIUM",
        "risk_reason": "Tree planting as offset is controversial. SBTi Net-Zero Standard discourages reliance on offsets over direct emission cuts.",
        "discrepancy_flag": False,
        "discrepancy_pair": None,
    },
]

DEMO_FACT_RESULTS = [
    {
        "claim_id": "claim-001",
        "text": DEMO_CLAIMS[0]["text"],
        "verification_status": "unverified",
        "alignment_score": 0.18,
        "method": "rag",
        "source_snippet": "SBTi defines 'carbon neutrality' as achieving net GHG impact of zero by balancing verified emissions with certified removals. Marketing claims relying solely on voluntary offsets are misleading.",
        "source_url": "https://sciencebasedtargets.org/resources/files/Net-Zero-Standard.pdf",
    },
    {
        "claim_id": "claim-002",
        "text": DEMO_CLAIMS[1]["text"],
        "verification_status": "partial",
        "alignment_score": 0.65,
        "method": "rag",
        "source_snippet": "CDP data: only 1 in 200 companies globally has achieved verified 100% renewable electricity sourcing (RE100). 45% increase needs PPA/REC documentation.",
        "source_url": "https://www.cdp.net/en",
    },
    {
        "claim_id": "claim-003",
        "text": DEMO_CLAIMS[2]["text"],
        "verification_status": "unverified",
        "alignment_score": 0.22,
        "method": "rag",
        "source_snippet": "IPCC AR6: Global emissions must fall by 43% by 2030 relative to 2019. Corporate net-zero claims targeting 2050 without interim 2030 milestones are inconsistent with IPCC timelines.",
        "source_url": "https://www.ipcc.ch/report/ar6/wg3/",
    },
    {
        "claim_id": "claim-004",
        "text": DEMO_CLAIMS[3]["text"],
        "verification_status": "partial",
        "alignment_score": 0.48,
        "method": "rag",
        "source_snippet": "UNGPs state companies must conduct ongoing human rights due diligence across supply chains. Claims of 'responsible sourcing' without published audit results are non-compliant.",
        "source_url": "https://www.unglobalcompact.org/what-is-gc/our-work/social/human-rights",
    },
    {
        "claim_id": "claim-005",
        "text": DEMO_CLAIMS[4]["text"],
        "verification_status": "partial",
        "alignment_score": 0.52,
        "method": "rag",
        "source_snippet": "AWS Standard: Claims of 'water positive' require site-level water accounting verified against local watershed baselines. Company-wide statements without facility data don't meet AWS requirements.",
        "source_url": "https://a4ws.org/the-aws-standard/",
    },
    {
        "claim_id": "claim-006",
        "text": DEMO_CLAIMS[5]["text"],
        "verification_status": "verified",
        "alignment_score": 0.82,
        "method": "rag",
        "source_snippet": "CDP 2023: The global avg Scope 1 reduction rate across Fortune 500 is 3.1% YoY. A 62% cumulative reduction from 2019 (roughly 12.4%/yr) is high but achievable with significant CapEx.",
        "source_url": "https://www.cdp.net/en/research/global-reports",
    },
    {
        "claim_id": "claim-007",
        "text": DEMO_CLAIMS[6]["text"],
        "verification_status": "unverified",
        "alignment_score": 0.12,
        "method": "web",
        "source_snippet": "No independent governance ranking or certification was found to support 'best-in-class' designation. Company is not listed in DJSI or MSCI ESG Leaders Index.",
        "source_url": "https://www.spglobal.com/esg/csa/",
    },
    {
        "claim_id": "claim-008",
        "text": DEMO_CLAIMS[7]["text"],
        "verification_status": "partial",
        "alignment_score": 0.41,
        "method": "web",
        "source_snippet": "SBTi Net-Zero Standard: Companies should prioritize direct emission cuts (90%+) over offsetting. Tree-planting offsets face permanence, additionality, and double-counting challenges.",
        "source_url": "https://sciencebasedtargets.org/net-zero",
    },
]


def _build_reasoning_trail(job_id: str) -> list[dict]:
    """Build a realistic reasoning trail with timestamps."""
    base_time = datetime.utcnow()
    trail = [
        {"agent": "harvester", "action": "PDF Ingestion Started", "detail": f"Parsing uploaded ESG report ({job_id[:8]}…)", "severity": "info"},
        {"agent": "harvester", "action": "Text Extracted", "detail": "Extracted 4,231 words across 16 pages. OCR not needed — text layer present.", "severity": "info"},
        {"agent": "harvester", "action": "Claims Identified", "detail": f"Found {len(DEMO_CLAIMS)} ESG-related claims via NLP chunking.", "severity": "info"},
        {"agent": "social_monitor", "action": "Social Scraping Started", "detail": "Crawling company LinkedIn feed with Crawl4AI stealth browser.", "severity": "info"},
        {"agent": "social_monitor", "action": "Posts Collected", "detail": f"Scraped {len(DEMO_SOCIAL_POSTS)} recent posts with sustainability keywords.", "severity": "info"},
        {"agent": "auditor", "action": "ClimateBERT Analysis", "detail": "Running climate sentiment classification on all claims.", "severity": "info"},
        {"agent": "auditor", "action": "⚠️ High Sentiment Detected", "detail": "claim-001: Sentiment 0.92 with ZERO quantification → HIGH RISK", "severity": "warning"},
        {"agent": "auditor", "action": "⚠️ Superlative Language", "detail": "claim-007: 'Best-in-class' without supporting evidence → HIGH RISK", "severity": "warning"},
        {"agent": "auditor", "action": "🔴 Discrepancy Found", "detail": "PDF claims 100% carbon neutrality vs social post says 'journey to carbon neutrality' — contradiction.", "severity": "flag"},
        {"agent": "fact_checker", "action": "RAG Search", "detail": "Querying ChromaDB with SBTi/CDP/IPCC benchmarks for 8 claims.", "severity": "info"},
        {"agent": "fact_checker", "action": "🔴 Unverified Claim", "detail": "claim-001: Carbon neutrality claim does NOT align with SBTi Net-Zero Standard (score: 0.18).", "severity": "flag"},
        {"agent": "fact_checker", "action": "✅ Verified Claim", "detail": "claim-006: 62% Scope 1+2 reduction is consistent with CDP benchmarks (score: 0.82).", "severity": "info"},
        {"agent": "judge", "action": "Scoring Complete", "detail": "Greenwash Index: 67.4 / 100 — HIGH RISK. 3 high-risk claims, 3 discrepancies identified.", "severity": "flag"},
    ]

    for i, entry in enumerate(trail):
        entry["timestamp"] = (base_time + timedelta(seconds=i * 2)).isoformat()

    return trail


def _build_final_report() -> dict:
    """Build the final greenwash index report."""
    high = sum(1 for a in DEMO_AUDIT_RESULTS if a["risk_level"] == "HIGH")
    medium = sum(1 for a in DEMO_AUDIT_RESULTS if a["risk_level"] == "MEDIUM")
    low = sum(1 for a in DEMO_AUDIT_RESULTS if a["risk_level"] == "LOW")
    verified = sum(1 for f in DEMO_FACT_RESULTS if f["verification_status"] == "verified")
    discrepancies = sum(1 for a in DEMO_AUDIT_RESULTS if a["discrepancy_flag"])

    return {
        "greenwash_index": 67.4,
        "risk_band": "HIGH",
        "total_claims": len(DEMO_CLAIMS),
        "high_risk_count": high,
        "medium_risk_count": medium,
        "low_risk_count": low,
        "verified_count": verified,
        "discrepancy_count": discrepancies,
        "summary": (
            "Acme Corp's ESG report contains 8 analyzed claims. 3 are flagged HIGH RISK due to "
            "vague language, unsupported superlatives, and missing Scope 3 disclosures. "
            "Only 1 out of 8 claims (Scope 1+2 reduction) was fully verified against SBTi/CDP benchmarks. "
            "3 discrepancies were detected between PDF claims and social media messaging — notably, "
            "the PDF states '100% carbon neutrality' while LinkedIn describes it as a 'journey', "
            "suggesting the achievement is aspirational, not realized. Overall Greenwash Index: 67.4 (HIGH RISK)."
        ),
    }


async def run_demo_swarm(job_id: str, pdf_path: str, company_url: str | None, on_trail=None) -> dict:
    """
    Simulate the full swarm pipeline with realistic delays and trail entries.
    Returns a dict matching SwarmState fields.
    """
    logger.info("🎭 Running DEMO swarm for job %s", job_id)

    trail = _build_reasoning_trail(job_id)

    # Simulate progressive processing with delays
    for i, entry in enumerate(trail):
        if on_trail:
            on_trail(entry)
        # Faster delays for demo: 0.4–0.8s per step
        await asyncio.sleep(random.uniform(0.4, 0.8))

    return {
        "pdf_path": pdf_path,
        "company_url": company_url,
        "job_id": job_id,
        "raw_text": "[Demo mode — PDF text extraction simulated]",
        "claims": DEMO_CLAIMS,
        "social_posts": DEMO_SOCIAL_POSTS,
        "screenshots": [],
        "audit_results": DEMO_AUDIT_RESULTS,
        "fact_results": DEMO_FACT_RESULTS,
        "final_report": _build_final_report(),
        "reasoning_trail": trail,
        "error": None,
        "status": "done",
    }
