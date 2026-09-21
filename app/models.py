from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator


def utcnow():
    return datetime.now(timezone.utc)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NewsSource(Model):
    title: str
    url: str
    snippet: str = ""
    published_at: AwareDatetime | None = None
    source: str = ""
    content: str = ""
    date_evidence: str = ""
    date_precision: Literal["exact", "day", "unknown"] = "unknown"
    fetched: bool = False
    fetch_error: str = ""


class Evidence(Model):
    text: str
    source_urls: list[str] = Field(min_length=1)
    quote: str = Field(min_length=1)


class KeyNumber(Evidence):
    status: Literal["FACT", "COMPANY CLAIM"]


class CandidateEvent(Model):
    id: str
    title: str
    short_description: str
    category: Literal["model", "update", "research", "tool", "pricing", "open_source"]
    event_kind: Literal["release", "update", "benchmark", "pricing", "research"]
    published_at: AwareDatetime | None = None
    sources: list[NewsSource] = Field(min_length=1)
    potential_significance: str
    potential_significance_score: float = Field(default=5, ge=0, le=10)
    entities: list[str] = Field(min_length=1)


class Verification(Model):
    verified: bool
    occurred_at: AwareDatetime | None
    date_source_url: str
    date_quote: str
    primary_source_url: str
    independent_source_urls: list[str]
    confirmed_facts: list[Evidence]
    company_claims: list[Evidence]
    unverified_claims: list[Evidence]
    key_numbers: list[KeyNumber]
    conflicts: list[str]
    confidence: float = Field(ge=0, le=10)
    reason: str


class VerifiedEvent(Model):
    candidate: CandidateEvent
    verification: Verification
    sources: list[NewsSource]


class ContextAnalysis(Model):
    previous_state: list[Evidence]
    what_changed: str
    hype: Literal["LOW", "MODERATE", "HIGH"]
    hype_reason: str
    limitations: list[str]


class Scores(Model):
    importance: float = Field(ge=0, le=10)
    novelty: float = Field(ge=0, le=10)
    practicality: float = Field(ge=0, le=10)
    impact: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=10)


class ImpactAnalysis(Model):
    scores: Scores
    what_happened: str
    why_it_matters: str
    practical_opportunities: list[str]
    product_impact: str
    what_to_try: str
    alfa_bank_relevance: str
    inference_limitations: list[str]


class AnalyzedEvent(Model):
    event: VerifiedEvent
    context: ContextAnalysis
    context_sources: list[NewsSource]
    impact: ImpactAnalysis
    significance_score: float = Field(ge=0, le=10)


class Exclusion(Model):
    id: str
    reason: str


class Editorial(Model):
    selected_ids: list[str]
    summary: str
    market_trend: str
    trend_event_ids: list[str]
    excluded: list[Exclusion]


class Usage(Model):
    agent: str
    model: str
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = None
    duration: float = 0
    timestamp: AwareDatetime = Field(default_factory=utcnow)
    success: bool = True


class FinalDigest(Model):
    run_id: str
    started_at: AwareDatetime
    window_start: AwareDatetime
    window_end: AwareDatetime
    mock: bool
    summary: str
    market_trend: str
    events: list[AnalyzedEvent]
    unconfirmed: list[VerifiedEvent]
    usage: list[Usage]
    warnings: list[str]

    @model_validator(mode="after")
    def validate_events(self):
        for event in self.events:
            v = event.event.verification
            if not v.verified or v.occurred_at is None or not self.window_start <= v.occurred_at <= self.window_end:
                raise ValueError("Digest may contain only verified in-window events")
        return self
