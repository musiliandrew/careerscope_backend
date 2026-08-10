from datetime import datetime
from pydantic import BaseModel, Field

class CapabilityBelief(BaseModel):
    """
    Inferred understanding of a user's capability derived from Features.
    Contains explicit uncertainty metrics.
    """
    capability_id: str = Field(..., description="Ontology ID, e.g., 'cap_backend_engineering'")
    
    score: float = Field(default=0.0, ge=0.0, le=100.0, description="Inferred strength (0-100)")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="How certain we are (0-1)")
    uncertainty: float = Field(default=1.0, ge=0.0, le=1.0, description="1.0 - confidence")
    
    evidence_count: int = Field(default=0, description="Number of distinct evidence items supporting this belief")
    freshness: float = Field(default=0.0, ge=0.0, le=1.0, description="Recency score of the underlying evidence")
    stability: float = Field(default=0.0, ge=0.0, le=1.0, description="How consistent the evidence is over time")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_actionable(self) -> bool:
        """Determines if the platform has enough certainty to recommend actions based on this belief."""
        return self.confidence > 0.6
