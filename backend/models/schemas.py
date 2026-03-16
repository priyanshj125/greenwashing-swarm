"""
Pydantic Schemas — API request/response models
"""
from pydantic import BaseModel
from typing import List, Optional


class AnalyzeRequest(BaseModel):
    company_url: Optional[str] = None    # optional LinkedIn/newsroom URL


class SocialPostOut(BaseModel):
    text: str
    date: str
    url: str
    platform: str
    screenshot_path: Optional[str]
    sentiment_keywords: List[str]


class AuditResultOut(BaseModel):
    claim_id: str
    text: str
    source: str
    climate_sentiment: float
    esg_category: str
    has_numbers: bool
    risk_level: str
    risk_reason: str
    discrepancy_flag: bool
    discrepancy_pair: Optional[dict]


class FactResultOut(BaseModel):
    claim_id: str
    text: str
    verification_status: str
    alignment_score: float
    method: str
    source_snippet: str
    source_url: str


class TrailEntryOut(BaseModel):
    agent: str
    timestamp: str
    action: str
    detail: str
    severity: str


class FinalReportOut(BaseModel):
    greenwash_index: float
    risk_band: str
    total_claims: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    verified_count: int
    discrepancy_count: int
    summary: str


class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    final_report: Optional[FinalReportOut]
    audit_results: List[AuditResultOut]
    fact_results: List[FactResultOut]
    reasoning_trail: List[TrailEntryOut]
    social_posts: List[SocialPostOut]
    screenshots: List[str]


class StatusEvent(BaseModel):
    job_id: str
    status: str
    detail: str
    agent: Optional[str]
