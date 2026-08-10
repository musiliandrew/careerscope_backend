import hashlib
import json
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class SemanticCache:
    """
    Prevents duplicate AI calls by caching identical Reasoning Traces.
    Currently a stub; eventually backed by Redis.
    """
    def __init__(self):
        self._memory_cache: Dict[str, Any] = {}
        
    def _generate_key(self, prompt_name: str, variables: Dict[str, Any]) -> str:
        # Sort keys to ensure deterministic hashing
        payload = json.dumps(variables, sort_keys=True)
        key_content = f"{prompt_name}:{payload}"
        return hashlib.sha256(key_content.encode('utf-8')).hexdigest()

    async def get(self, prompt_name: str, variables: Dict[str, Any], response_model: Type[T]) -> Optional[T]:
        key = self._generate_key(prompt_name, variables)
        cached_data = self._memory_cache.get(key)
        
        if cached_data:
            return response_model.model_validate(cached_data)
        return None
        
    async def set(self, prompt_name: str, variables: Dict[str, Any], result: BaseModel):
        key = self._generate_key(prompt_name, variables)
        self._memory_cache[key] = result.model_dump(mode="json")
