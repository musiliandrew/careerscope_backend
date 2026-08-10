import pytest
from pydantic import BaseModel
from shared.ai.guardrails import Guardrails

class MockResponse(BaseModel):
    confidence: float

def test_guardrails_normalizes_confidence():
    # Out of bounds high
    resp = MockResponse(confidence=1.5)
    validated = Guardrails.validate(resp)
    assert validated.confidence == 1.0
    
    # Out of bounds low
    resp_low = MockResponse(confidence=-0.5)
    validated_low = Guardrails.validate(resp_low)
    assert validated_low.confidence == 0.0
    
    # Normal
    resp_norm = MockResponse(confidence=0.8)
    validated_norm = Guardrails.validate(resp_norm)
    assert validated_norm.confidence == 0.8
