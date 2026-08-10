import pytest
import asyncio
from shared.ai.retry import RetryPolicy

@pytest.mark.asyncio
async def test_retry_policy_success_first_try():
    policy = RetryPolicy(max_retries=3, base_delay_ms=10)
    
    async def primary():
        return "success"
        
    result = await policy.execute_with_fallback(primary, [])
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_policy_fallback_success():
    policy = RetryPolicy(max_retries=1, base_delay_ms=10)
    
    attempts = {'primary': 0}
    
    async def primary():
        attempts['primary'] += 1
        raise ValueError("Primary Failed")
        
    async def fallback():
        return "fallback_success"
        
    result = await policy.execute_with_fallback(primary, [fallback])
    
    # Primary should fail twice (initial + 1 retry)
    assert attempts['primary'] == 2
    assert result == "fallback_success"
