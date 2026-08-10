from pydantic import BaseModel, Field

class Capability(BaseModel):
    """
    A Capability is an aggregate concept encompassing skills and technologies.
    This is what the inference layer evaluates.
    """
    id: str = Field(..., description="Canonical ID, e.g., 'cap_backend_engineering'")
    name: str = Field(..., description="Canonical name, e.g., 'Backend Engineering'")
    related_skills: list[str] = Field(default_factory=list, description="List of Skill IDs")
    related_technologies: list[str] = Field(default_factory=list, description="List of Technology IDs")
