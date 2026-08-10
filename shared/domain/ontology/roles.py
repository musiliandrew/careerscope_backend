from pydantic import BaseModel, Field

class RoleLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    
class Role(BaseModel):
    """
    Canonical representation of a Job Role.
    """
    id: str = Field(..., description="Canonical ID, e.g., 'role_ml_engineer'")
    name: str = Field(..., description="Canonical name, e.g., 'Machine Learning Engineer'")
    level_agnostic_id: str = Field(..., description="e.g., 'role_family_swe'")
    core_capabilities: list[str] = Field(default_factory=list, description="Required Capability IDs")
