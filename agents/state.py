"""
Greenwash Swarm — Shared LangGraph State
All agents read from and write to SwarmState.
"""
from typing import TypedDict, List, Optional, Annotated
import operator


class SocialPost(TypedDict):
    text: str
    date: str
    url: str
    platform: str
    screenshot_path: Optional[str]
    sentiment_keywords: List[str]


class ClaimResult(TypedDict):
    id: str
    text: str
    page: int
    source: str          # "pdf" | "social"
    esg_category: str    # Environmental | Social | Governance | Neutral
    has_numbers: bool
    materiality_tag: str # e.g., "carbon", "water", "supply_chain"


class AuditResult(TypedDict):
    claim_id: str
    text: str
    source: str
    climate_sentiment: float         # 0.0–1.0
    esg_category: str
    has_numbers: bool
    risk_level: str                  # HIGH | MEDIUM | LOW | NEUTRAL
    risk_reason: str
    discrepancy_flag: bool           # True if PDF vs Social contradiction found
    discrepancy_pair: Optional[dict] # {pdf_claim, social_claim, score}


class FactResult(TypedDict):
    claim_id: str
    text: str
    verification_status: str    # verified | partial | unverified
    alignment_score: float      # 0.0–1.0 (1.0 = perfect match with benchmark)
    method: str                 # rag | web | none
    source_snippet: str
    source_url: str


class TrailEntry(TypedDict):
    agent: str          # harvester | social_monitor | auditor | fact_checker | judge
    timestamp: str
    action: str
    detail: str
    severity: str       # info | warning | flag


class FinalReport(TypedDict):
    greenwash_index: float           # 0–100
    risk_band: str                   # LOW | MEDIUM | HIGH | CRITICAL
    total_claims: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    verified_count: int
    discrepancy_count: int
    summary: str


class SwarmState(TypedDict):
    # Input
    pdf_path: str
    company_url: Optional[str]              # LinkedIn/newsroom URL for social scraping
    job_id: str

    # Agent A1 — Harvester outputs
    raw_text: str
    claims: Annotated[List[ClaimResult], operator.add]

    # Agent A2 — Social Monitor outputs
    social_posts: List[SocialPost]
    screenshots: List[str]                  # saved screenshot artifact paths

    # Agent B — Auditor outputs
    audit_results: Annotated[List[AuditResult], operator.add]

    # Agent C — Fact-Checker outputs
    fact_results: Annotated[List[FactResult], operator.add]

    # Agent D — Judge outputs
    final_report: Optional[FinalReport]
    reasoning_trail: Annotated[List[TrailEntry], operator.add]

    # Control
    error: Optional[str]
    status: str        # queued | harvesting | auditing | fact_checking | judging | done | error
