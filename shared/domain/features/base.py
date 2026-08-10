from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

T = TypeVar('T')

class Feature(BaseModel, Generic[T]):
    """
    Immutable, objective, measurable observations.
    """
    id: str = Field(..., description="e.g., 'feat_github_commits_last_12m'")
    version: int = Field(default=1, description="Algorithm version used to compute this feature")
    value: T
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_ids: list[UUID] = Field(default_factory=list, description="IDs of evidence used to compute this fact")

class FeatureStore(BaseModel):
    """
    A collection of computed facts for a user at a point in time.
    """
    user_id: UUID
    features: dict[str, Feature] = Field(default_factory=dict)
    
    def get(self, feature_id: str) -> Feature | None:
        return self.features.get(feature_id)
