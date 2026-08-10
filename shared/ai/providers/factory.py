from shared.config.decision import DecisionSettings
from shared.ai.providers.base import LLMProvider
from shared.ai.providers.gemini import GeminiProvider

class ProviderFactory:
    """
    Instantiates AI Providers. No application code should instantiate providers directly.
    """
    
    @staticmethod
    def create(provider_name: str, settings: DecisionSettings) -> LLMProvider:
        """
        Creates a provider by name (e.g., 'gemini', 'openrouter').
        """
        if provider_name.lower() == "gemini":
            return GeminiProvider(settings)
        # elif provider_name.lower() == "openrouter":
        #     return OpenRouterProvider(settings)
        # elif provider_name.lower() == "ollama":
        #     return OllamaProvider(settings)
        else:
            raise ValueError(f"Unknown LLM Provider: {provider_name}")
