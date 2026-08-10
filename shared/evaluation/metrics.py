from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class ReasoningEvaluation(BaseModel):
    """
    Quantitative and Qualitative evaluation of a single reasoning execution.
    This tracks the performance, cost, and quality of AI pipeline responses over time.
    """
    request_id: UUID
    prompt_version: str
    model_version: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Execution Metrics
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    cache_hit: bool = False
    retry_count: int = 0
    
    # Automated Quality Metrics
    schema_valid: bool = True
    confidence_calibration: float = Field(default=0.0, ge=0.0, le=1.0, description="How bounded/realistic the confidence score was")
    recommendation_stability: float = Field(default=0.0, ge=0.0, le=1.0, description="Similarity to known golden examples")
    
    # Manual / Human-in-the-loop Metrics
    explanation_consistency: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Human score for explanation clarity")
    hallucination_detected: Optional[bool] = None
    reviewer_notes: Optional[str] = None
