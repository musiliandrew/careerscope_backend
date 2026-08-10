import logging
from typing import Type, TypeVar, Any, Dict
from pydantic import BaseModel

from shared.config.decision import DecisionSettings
from shared.ai.prompts.registry import PromptRegistry
from shared.ai.providers.factory import ProviderFactory
from shared.ai.retry import RetryPolicy
from shared.ai.cache import SemanticCache
from shared.ai.guardrails import Guardrails
from shared.ai.observability import ExecutionContext

T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)

class AIExecutor:
    """
    The Unified Orchestrator for all AI interactions.
    Handles caching, retries, fallback routing, telemetry, and guardrails.
    """
    def __init__(self, settings: DecisionSettings):
        self.settings = settings
        self.cache = SemanticCache()
        self.retry_policy = RetryPolicy()
        
        # Instantiate primary and fallback providers
        self.primary_provider = ProviderFactory.create(self.settings.ai_primary, self.settings)
        
        self.fallback_providers = []
        if self.settings.ai_fallback:
            self.fallback_providers.append(
                ProviderFactory.create(self.settings.ai_fallback, self.settings)
            )

    async def execute(
        self,
        prompt_name: str,
        response_model: Type[T],
        variables: Dict[str, Any]
    ) -> T:
        """
        Orchestrates an AI request from end to end.
        """
        # 1. Check Cache
        cached_response = await self.cache.get(prompt_name, variables, response_model)
        if cached_response:
            logger.info(f"Cache hit for prompt: {prompt_name}")
            return cached_response

        # 2. Load Prompt
        prompt_bundle = PromptRegistry.load(prompt_name)

        # 3. Initialize Telemetry Context
        context = ExecutionContext(
            provider=self.settings.ai_primary,
            model=prompt_bundle.model,
            prompt_version=f"{prompt_bundle.name}.v{prompt_bundle.version}",
            temperature=prompt_bundle.temperature,
            started_at=None, # set inside provider
            finished_at=None
        )

        # 4. Define Provider Calls
        async def call_primary():
            context.provider = self.settings.ai_primary
            return await self.primary_provider.generate(prompt_bundle, response_model, context, variables)
            
        fallback_calls = []
        for fb_provider, fb_name in zip(self.fallback_providers, [self.settings.ai_fallback]):
            async def call_fallback(p=fb_provider, n=fb_name):
                context.provider = n
                return await p.generate(prompt_bundle, response_model, context, variables)
            fallback_calls.append(call_fallback)

        # 5. Execute with Retries & Fallbacks
        raw_result = await self.retry_policy.execute_with_fallback(call_primary, fallback_calls)

        # 6. Guardrails Validation
        validated_result = Guardrails.validate(raw_result)

        # 7. Update Cache
        await self.cache.set(prompt_name, variables, validated_result)

        # 8. Emit Telemetry (e.g., to Langfuse)
        context.calculate_duration()
        logger.info(f"AI Execution Completed. Latency: {context.latency_ms}ms, Provider: {context.provider}")

        return validated_result
