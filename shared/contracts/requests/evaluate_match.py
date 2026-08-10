from typing import List, Dict, Any
from pydantic import BaseModel
from shared.contracts.responses.mission import IntelligenceSnapshot
from shared.domain.evidence import Evidence

class JobRequirementSnapshot(BaseModel):
    """Stateless representation of a job passed to the Decision Engine."""
    title: str
    company_name: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    description: str

class EvaluateMatchRequest(BaseModel):
    """
    Request payload sent to the Decision Engine to evaluate a candidate against a job.
    Includes all necessary state (pure function input).
    """
    profile_snapshot: IntelligenceSnapshot
    job_snapshot: JobRequirementSnapshot
    relevant_evidence: List[Evidence]
