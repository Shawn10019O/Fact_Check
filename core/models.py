from dataclasses import dataclass, field
from typing import List

@dataclass
class SuspiciousClaifm:
    text: str
    evidence_urls: List[str] = field(default_factory=list)

@dataclass
class SlideResult:
    slide_no: int
    raw_text: str
    cleaned_text: str
    verdict: str          
    rationale: str
    suspicious_claims: List[SuspiciousClaifm] = field(default_factory=list)
