from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Capability(BaseModel):
    """
    Pure domain representation of an extracted capability (Intelligence).
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="e.g., 'Python', 'System Design'")
    category: Optional[str] = None
    
    # Raw Features (0-100 scales)
    verification_score: float = Field(default=0.0, ge=0.0, le=100.0)
    depth_score: float = Field(default=0.0, ge=0.0, le=100.0)
    freshness_score: float = Field(default=0.0, ge=0.0, le=100.0)
    market_relevance: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Intrinsic value
    capability_score: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Provenance
    supported_by_evidence_ids: List[UUID] = Field(default_factory=list)
    parent_capability_ids: List[UUID] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
