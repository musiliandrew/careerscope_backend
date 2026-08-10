import logging
import asyncio
from typing import Callable, Any, TypeVar, List

T = TypeVar('T')
logger = logging.getLogger(__name__)

class RetryPolicy:
    """
    Orchestrates retries and failovers across multiple providers.
    """
    def __init__(self, max_retries: int = 3, base_delay_ms: int = 500):
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms

    async def execute_with_fallback(
        self,
        primary_callable: Callable[[], Any],
        fallback_callables: List[Callable[[], Any]]
    ) -> T:
        """
        Executes the primary provider with retries. If all retries fail, attempts fallbacks sequentially.
        """
        callables = [primary_callable] + fallback_callables
        
        for attempt, func in enumerate(callables):
            provider_retries = 0
            while provider_retries <= self.max_retries:
                try:
                    return await func()
                except Exception as e:
                    provider_retries += 1
                    logger.warning(f"Provider call failed (Attempt {provider_retries}/{self.max_retries}): {str(e)}")
                    
                    if provider_retries > self.max_retries:
                        logger.error("Provider exhausted all retries.")
                        break # Move to next fallback callable
                    
                    delay = (self.base_delay_ms / 1000.0) * (2 ** (provider_retries - 1))
                    await asyncio.sleep(delay)
                    
        raise RuntimeError("All providers and retries failed.")
