import os
from typing import Dict, Any

from .GeminiAI import extract_resume as gemini_extract_resume
from .OpenRouterAI import extract_resume as openrouter_extract_resume


class AIManager:
    def __init__(self, primary: str | None = None, fallback: str | None = None):
        self.primary = (primary or os.getenv("AI_PRIMARY") or "gemini").lower()
        self.fallback = (fallback or os.getenv("AI_FALLBACK") or "openrouter").lower()

    def _run_provider(self, provider: str, text: str) -> Dict[str, Any]:
        if provider == "gemini":
            return gemini_extract_resume(text)
        if provider == "openrouter":
            return openrouter_extract_resume(text)
        raise ValueError(f"Unknown AI provider: {provider}")

    def extract_resume(self, text: str) -> Dict[str, Any]:
        errors: list[str] = []
        for provider in [self.primary, self.fallback]:
            if not provider:
                continue
            try:
                result = self._run_provider(provider, text)
                if result and isinstance(result, dict):
                    result.setdefault("provider", provider)
                    return result
            except Exception as e:
                errors.append(f"{provider}: {e}")
                continue
        # If everything fails, return a minimal safe payload
        return {
            "header": {},
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "extras": {},
            "confidence": 0.0,
            "errors": errors,
        }
