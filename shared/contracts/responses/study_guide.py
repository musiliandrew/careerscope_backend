from pydantic import BaseModel, Field
from typing import List

class StudyGuideResult(BaseModel):
    encouraging_message: str = Field(..., description="A short, agentic message acting as a career coach with context of memory.")
    core_weaknesses: List[str] = Field(..., description="The main areas to improve based on the feedback.")
    action_plan: List[str] = Field(..., description="Actionable 30-day study goals or steps.")
