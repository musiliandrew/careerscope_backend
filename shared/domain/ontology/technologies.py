from enum import Enum
from pydantic import BaseModel, Field

class TechCategory(str, Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    TOOL = "tool"

class Technology(BaseModel):
    """
    Canonical representation of a specific Technology.
    """
    id: str = Field(..., description="Canonical ID, e.g., 'tech_python'")
    name: str = Field(..., description="Canonical name, e.g., 'Python'")
    category: TechCategory
    aliases: list[str] = Field(default_factory=list, description="e.g., ['python3', 'py']")
