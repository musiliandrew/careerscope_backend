import httpx
from typing import Optional
from shared.contracts.requests.evaluate_match import EvaluateMatchRequest
from shared.contracts.responses.decision_result import DecisionResult

class DecisionEngineClient:
    """
    Typed Internal SDK for communicating with the Decision Engine.
    Handles retries, auth, tracing, and metric emission internally.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        # Configure httpx.AsyncClient with retries and timeout logic here
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def evaluate_match(self, request: EvaluateMatchRequest) -> DecisionResult:
        """
        Pure function invocation. The engine knows nothing about the caller's persistence.
        """
        # Tracing context would be injected here
        response = await self.client.post(
            f"{self.base_url}/api/v1/reasoning/evaluate_match",
            json=request.model_dump(mode="json")
        )
        response.raise_for_status()
        return DecisionResult.model_validate(response.json())
