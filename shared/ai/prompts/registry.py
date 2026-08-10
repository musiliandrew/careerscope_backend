import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PromptBundle(BaseModel):
    name: str
    version: str
    owner: str
    temperature: float = 0.2
    model: str = "gemini"
    
    system_prompt: str
    user_template: str
    fewshot_examples: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PromptRegistry:
    """
    Centralized loader for AI prompts.
    Reads versioned prompts from the filesystem structure:
    prompts/{domain}/{name}/[system.md, user.md, metadata.yaml]
    """
    BASE_DIR = Path(__file__).parent
    
    @classmethod
    def get(cls, full_name: str) -> PromptBundle:
        """
        Alias for load.
        """
        # Automatically prepend namespace if missing for match_score
        if full_name == "match_score":
            full_name = "reasoning.match_score"
        return cls.load(full_name)

    @classmethod
    def load(cls, full_name: str) -> PromptBundle:
        """
        Load a prompt bundle.
        Example: PromptRegistry.load("reasoning.match_score")
        """
        # "reasoning.match_score" -> "reasoning/match_score"
        parts = full_name.split('.')
        prompt_dir = cls.BASE_DIR.joinpath(*parts)
        
        if not prompt_dir.exists():
            raise FileNotFoundError(f"Prompt '{full_name}' not found at {prompt_dir}")
            
        metadata_path = prompt_dir / "metadata.yaml"
        system_path = prompt_dir / "system.md"
        user_path = prompt_dir / "user.md"
        fewshot_path = prompt_dir / "fewshot.md"
        
        if not metadata_path.exists():
            raise ValueError(f"Missing metadata.yaml for prompt '{full_name}'")
            
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f) or {}
            
        with open(system_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
            
        with open(user_path, 'r', encoding='utf-8') as f:
            user_template = f.read().strip()
            
        fewshot = None
        if fewshot_path.exists():
            with open(fewshot_path, 'r', encoding='utf-8') as f:
                fewshot = f.read().strip()
                
        return PromptBundle(
            name=metadata.get('name', full_name),
            version=metadata.get('version', '1.0.0'),
            owner=metadata.get('owner', 'unknown'),
            temperature=metadata.get('temperature', 0.2),
            model=metadata.get('model', 'gemini'),
            system_prompt=system_prompt,
            user_template=user_template,
            fewshot_examples=fewshot,
            metadata=metadata
        )
