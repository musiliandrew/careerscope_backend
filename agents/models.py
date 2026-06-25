from pydantic import BaseModel


class Profile(BaseModel):
    full_name: str
    portfolio_url: str | None
    phone_number: str
    country: str | None
    linkedin_url: str | None
    education_background: list["Education"]
    skills: list["Skills"]


class Education(BaseModel):
    institution: str
    joined: str
    certification: str
    course: str
    completed: str


class Skills(BaseModel):
    skill_name: str
    skill_category: str
    proficiency_level: str | None = "Not Specified"
    years_of_experience: str | None = "Not Specified"


# ======================
# Company Ingestion Models
# ======================

class CompanyDetail(BaseModel):
    pass