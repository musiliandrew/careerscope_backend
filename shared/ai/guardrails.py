from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class Guardrails:
    """
    Common validation pipeline for all provider responses.
    """
    
    @staticmethod
    def validate(response: BaseModel) -> BaseModel:
        """
        Executes Safety and Business Logic validation on the parsed LLM output.
        """
        # 1. Pydantic validation is already handled by the provider (pydantic-ai)
        
        # 2. Safety Validation (e.g., checking for PII leakage, prompt injection reflection)
        # TODO: Implement safety heuristics
        
        # 3. Business Validation (e.g., confidence scores must be valid)
        if hasattr(response, 'confidence') and (response.confidence < 0 or response.confidence > 1):
            logger.warning("LLM generated out-of-bounds confidence score. Normalizing.")
            response.confidence = max(0.0, min(1.0, response.confidence))
            
        return response
