from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from shared.domain.capability import Capability
from shared.contracts.responses.mission import NavigatorAction

class ReasonedExplanation(BaseModel):
    """Explains exactly why the AI reached a specific conclusion."""
    conclusion: str
    evidence_ids_used: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning_trace: str

class DecisionResult(BaseModel):
    """
    Standardized response contract from the Decision Engine.
    Used for Match Scores, Trajectory Updates, etc.
    """
    overall_readiness: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Gap Analysis
    missing_capabilities: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    
    # Explainability
    explanations: List[ReasonedExplanation] = Field(default_factory=list)
    
    # Updated nodes the caller should persist
    updated_capabilities: List[Capability] = Field(default_factory=list)
    recommended_actions: List[NavigatorAction] = Field(default_factory=list)
