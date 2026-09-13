from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RuleResult(BaseModel):
    code: str
    name: str
    status: str
    severity: str
    message: str
    evidence: str = ""


class ScanResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    extracted_text: str
    extracted: dict[str, Any]
    results: list[RuleResult]
    score: float
    status: str
    report_url: str | None = None


class StatisticsResponse(BaseModel):
    total_scans: int
    compliant: int
    failed: int
    needs_review: int
    average_score: float
