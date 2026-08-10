from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class EvidenceRelationship(BaseModel):
    """Represents a connection between two pieces of evidence."""
    target_id: UUID
    relationship_type: str = Field(..., description="e.g., 'supports', 'demonstrates'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class Evidence(BaseModel):
    """
    Pure domain representation of proof (e.g., Repo, PDF, URL).
    """
    id: UUID = Field(default_factory=uuid4)
    node_type: str = Field(..., description="'repository', 'publication', 'assessment', 'url'")
    source: str = Field(..., description="'github', 'linkedin', 'user_upload'")
    url: Optional[str] = None
    
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    relationships: List[EvidenceRelationship] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
