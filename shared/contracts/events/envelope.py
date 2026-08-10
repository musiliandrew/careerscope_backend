from datetime import datetime, timezone
from typing import Any, Dict, Generic, TypeVar, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

T = TypeVar('T', bound=BaseModel)

class EventEnvelope(BaseModel, Generic[T]):
    """
    Standardized Event Envelope for all Pub/Sub communication across the 6 domains.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the event instance")
    event_name: str = Field(..., description="The fully qualified name of the event (e.g., 'resume.uploaded')")
    version: int = Field(default=1, description="Schema version of the event payload")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of event creation")
    correlation_id: Optional[UUID] = Field(default=None, description="ID connecting a chain of events (e.g., the original request ID)")
    causation_id: Optional[UUID] = Field(default=None, description="ID of the specific event that directly caused this event")
    source: str = Field(..., description="The service publishing the event (e.g., 'backend', 'discovery')")
    payload: T = Field(..., description="The strictly typed Pydantic model for the event data")
