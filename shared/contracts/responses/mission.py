from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from shared.domain.capability import Capability

class NavigatorAction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sequence_order: int
    action_type: str = Field(..., description="e.g., 'verify_skill', 'build_project'")
    title: str
    description: Optional[str] = None
    roi_impact_percentage: float = Field(default=0.0)
    is_completed: bool = False

class IntelligenceSnapshot(BaseModel):
    """
    System artifact representing the state of intelligence at a specific point in time.
    """
    id: UUID = Field(default_factory=uuid4)
    version: int
    previous_snapshot_id: Optional[UUID] = None
    
    target_role: str
    career_readiness: float = Field(default=0.0, ge=0.0, le=100.0)
    estimated_time_months: Optional[int] = None
    
    capabilities: List[Capability] = Field(default_factory=list)
    navigator_plan: List[NavigatorAction] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
