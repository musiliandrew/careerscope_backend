from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any, Dict
from pydantic import BaseModel
from shared.ai.observability import ExecutionContext
from shared.ai.prompts.registry import PromptBundle

T = TypeVar('T', bound=BaseModel)

class LLMProvider(ABC):
    """
    Abstract Base Class for all AI Providers (Gemini, OpenRouter, etc.).
    Guarantees that no service depends on a specific LLM implementation.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: PromptBundle,
        response_model: Type[T],
        context: ExecutionContext,
        variables: Dict[str, Any]
    ) -> T:
        """
        Executes a prompt against the provider and returns a validated Pydantic model.
        MUST handle its own retries, timeouts, and populate the ExecutionContext.
        """
        pass
    
    @abstractmethod
    async def stream(self):
        """Future implementation for streaming responses."""
        pass
