from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Any

class ExecutionContext(BaseModel):
    """
    Universal execution record for all AI interactions.
    Every service must emit this to Langfuse/Tracing system upon completing an AI generation.
    """
    request_id: UUID = Field(default_factory=uuid4)
    correlation_id: Optional[UUID] = None
    
    provider: Optional[str] = Field(None, description="e.g., 'gemini', 'openrouter'")
    model: Optional[str] = Field(None, description="e.g., 'gemini-1.5-pro', 'claude-3-haiku'")
    prompt_version: Optional[str] = Field(None, description="e.g., 'explain_match.v1'")
    temperature: Optional[float] = None
    
    latency_ms: int = Field(default=0)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)
    
    cache_hit: bool = Field(default=False)
    retry_count: int = Field(default=0)
    
    started_at: Optional[Any] = None
    finished_at: Optional[Any] = None
    
    def calculate_duration(self):
        if not self.started_at or not self.finished_at:
            return
        if isinstance(self.started_at, (int, float)) and isinstance(self.finished_at, (int, float)):
            self.latency_ms = int((self.finished_at - self.started_at) * 1000)
        else:
            try:
                delta = self.finished_at - self.started_at
                self.latency_ms = int(delta.total_seconds() * 1000)
            except Exception:
                pass

