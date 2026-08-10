from pydantic import BaseModel, Field

class Company(BaseModel):
    """
    Canonical representation of a Company.
    """
    id: str = Field(..., description="Canonical ID, e.g., 'company_google'")
    name: str = Field(..., description="Canonical name, e.g., 'Google'")
    domains: list[str] = Field(default_factory=list, description="List of domain names e.g., ['google.com']")
    aliases: list[str] = Field(default_factory=list, description="e.g., ['Alphabet']")
