"""Pydantic schemas for the agentic evidence pipeline state and artifacts."""

from __future__ import annotations
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


RiskCategory = Literal[
    "dermatology_trichology",
    "orthodontics",
    "fitness",
    "surgical",
    "banned"
]


class ClaimVerification(BaseModel):
    claim: str
    evidence_found: bool
    source_pmid_or_doi: Optional[str] = None
    risk_level: Literal["safe", "caution", "prohibited"] = "safe"
    harm_reduction_note: Optional[str] = None


class EvidenceItem(BaseModel):
    compound: str
    indication: str
    route: Literal["topical", "oral", "physical", "systemic"]
    standard_dosage_numeric: float
    unit: str  # e.g., "%", "mg", "mcg", "mm"
    max_safe_limit: float
    efficacy_metric: str
    contraindications: List[str] = Field(default_factory=list)
    pmid: str
    doi: Optional[str] = None
    snippet: str


class EvidenceMatrix(BaseModel):
    discipline: str
    primary_compound: str
    items: List[EvidenceItem] = Field(default_factory=list)
    approved_pmids: List[str] = Field(default_factory=list)
    hard_contraindications: List[str] = Field(default_factory=list)


class FAQItem(BaseModel):
    question: str
    answer: str


class ArticleDraft(BaseModel):
    title: str
    slug: str
    target_kw: str
    audience_demographic: str = "Men 18-35"
    scientific_summary: str
    actionable_protocol: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    structured_faq: List[FAQItem] = Field(default_factory=list)


class AuditGateResult(BaseModel):
    passed: bool
    rejection_reason: Optional[str] = None
    failed_checks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    dosage_violations: List[str] = Field(default_factory=list)
    unverified_citations: List[str] = Field(default_factory=list)
    slang_or_toxic_detected: List[str] = Field(default_factory=list)
    can_auto_repair: bool = False


class PipelineState(BaseModel):
    raw_topic: str
    normalized_topic: str = ""
    risk_category: RiskCategory = "fitness"
    discipline_namespace: str = "general"
    retrieved_papers: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_matrix: Optional[EvidenceMatrix] = None
    verified_claims: List[ClaimVerification] = Field(default_factory=list)
    draft: Optional[ArticleDraft] = None
    audit_passed: bool = False
    rejection_reason: Optional[str] = None
    is_crisis_routed: bool = False
    crisis_payload: Optional[Dict[str, Any]] = None
    repair_attempts: int = 0
    max_repair_attempts: int = 2
    audit_history: List[AuditGateResult] = Field(default_factory=list)
    idempotency_key: Optional[str] = None
    step_history: List[str] = Field(default_factory=list)
    output_cms_markdown: Optional[str] = None
    output_json_ld: Optional[Dict[str, Any]] = None
