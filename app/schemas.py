from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


ConfidenceLabel = Literal['High', 'Medium', 'Low']


class ProfileDocument(BaseModel):
    profile_id: str
    name: str
    title: str | None = None
    department: str | None = None
    expertise_topics: list[str] = Field(default_factory=list)
    biography: str | None = None
    research_interests: str | None = None
    publications: str | None = None
    languages: list[str] = Field(default_factory=list)
    source_url: HttpUrl
    last_checked: str
    content_hash: str


class ProfileChunk(BaseModel):
    chunk_id: str
    profile_id: str
    name: str
    department: str | None = None
    title: str | None = None
    topics: list[str] = Field(default_factory=list)
    section: str
    text: str
    source_url: HttpUrl
    last_checked: str
    content_hash: str


class MediaEnquiry(BaseModel):
    enquiry_id: str | None = None
    sender_name: str
    sender_email: EmailStr
    outlet_name: str | None = None
    subject: str
    body: str


class VerificationResult(BaseModel):
    recognised_outlet: bool
    work_email_domain_match: bool
    freelancer_pathway: bool
    manual_review_required: bool
    notes: str


class RetrievedChunk(BaseModel):
    chunk_id: str
    profile_id: str
    name: str
    title: str | None = None
    department: str | None = None
    section: str
    text: str
    source_url: HttpUrl
    score: float
    topics: list[str] = Field(default_factory=list)


class ExpertRecommendation(BaseModel):
    profile_id: str
    name: str
    title: str | None = None
    department: str | None = None
    source_url: HttpUrl
    rationale: str
    supporting_chunks: list[RetrievedChunk]
    final_score: float
    topics: list[str] = Field(default_factory=list)
    confidence: ConfidenceLabel
    diversity_note: str | None = None


class RecommendationResponse(BaseModel):
    enquiry_id: str
    created_at: datetime
    verification: VerificationResult
    topic_labels: list[str]
    recommended_experts: list[ExpertRecommendation]
    requires_staff_approval: bool = True
    staff_summary: str | None = None


class ApprovalDecision(BaseModel):
    enquiry_id: str
    decision: str = Field(pattern='^(approved|rejected|manual_review)$')
    reviewer_name: str
    notes: str | None = None


class ApprovalRecord(BaseModel):
    enquiry_id: str
    decision: str
    reviewer_name: str
    notes: str | None = None
    created_at: datetime


class RetrievalAuditRecord(BaseModel):
    enquiry_id: str
    sender_email: EmailStr
    subject: str
    outlet_name: str | None = None
    topic_labels: list[str]
    verification: dict[str, Any]
    top_profile_ids: list[str]
