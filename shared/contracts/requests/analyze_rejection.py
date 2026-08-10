from pydantic import BaseModel, Field
from typing import List, Optional

class AnalyzeRejectionRequest(BaseModel):
    user_id: int
    company_name: str
    role_title: str
    missing_skills: List[str] = Field(default_factory=list)
    extracted_feedback: Optional[str] = None
