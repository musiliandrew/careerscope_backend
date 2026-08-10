from enum import Enum
from pydantic import BaseModel, Field

class SkillCategory(str, Enum):
    SOFT_SKILL = "soft_skill"
    TECHNICAL_PRACTICE = "technical_practice"
    DOMAIN_KNOWLEDGE = "domain_knowledge"

class Skill(BaseModel):
    """
    Canonical representation of a Skill (not tied to a specific technology).
    """
    id: str = Field(..., description="Canonical ID, e.g., 'skill_system_design'")
    name: str = Field(..., description="Human readable name, e.g., 'System Design'")
    category: SkillCategory
    aliases: list[str] = Field(default_factory=list)
