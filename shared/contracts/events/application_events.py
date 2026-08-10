from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class ApplicationReceivedPayload(BaseModel):
    user_id: int = Field(..., description="ID of the user who applied")
    company_name: str = Field(..., description="Company name")
    role_title: str = Field(..., description="Job role title")
    applied_at: datetime = Field(..., description="When the application was received/sent")
    source_email_id: Optional[str] = Field(None, description="Gmail Message ID")
    raw_email_snippet: Optional[str] = Field(None, description="Brief snippet of the email")

class InterviewInvitedPayload(BaseModel):
    user_id: int = Field(..., description="ID of the user invited")
    company_name: str = Field(..., description="Company name")
    role_title: str = Field(..., description="Job role title")
    interview_date: Optional[datetime] = Field(None, description="Extracted interview date/time if available")
    recruiter_name: Optional[str] = Field(None, description="Name of the person who reached out")
    source_email_id: Optional[str] = Field(None, description="Gmail Message ID")
    raw_email_snippet: Optional[str] = Field(None, description="Brief snippet of the email")

class ApplicationRejectedPayload(BaseModel):
    user_id: int = Field(..., description="ID of the user rejected")
    company_name: str = Field(..., description="Company name")
    role_title: str = Field(..., description="Job role title")
    rejected_at: datetime = Field(..., description="When the rejection was received")
    extracted_feedback: Optional[str] = Field(None, description="Any specific reasons or feedback provided")
    missing_skills: List[str] = Field(default_factory=list, description="Skills mentioned as lacking")
    source_email_id: Optional[str] = Field(None, description="Gmail Message ID")
    raw_email_snippet: Optional[str] = Field(None, description="Brief snippet of the email")
