from typing import Dict
from app.domain.interfaces.providers.base import AIGatewayProvider
from app.infrastructure.providers.openai_adapter import OpenAIAdapter
from app.infrastructure.providers.gemini_adapter import GeminiAdapter
from app.infrastructure.providers.groq_adapter import GroqAdapter
from app.infrastructure.providers.ollama_adapter import OllamaAdapter
from app.core.exceptions import ConfigurationException

class ProviderRegistry:
    _providers: Dict[str, AIGatewayProvider] = {}

    @classmethod
    def register_provider(cls, provider: AIGatewayProvider):
        cls._providers[provider.provider_name.lower()] = provider

    @classmethod
    def get_provider(cls, name: str) -> AIGatewayProvider:
        if name.lower() not in cls._providers:
            raise ConfigurationException(f"Provider {name} not found in registry")
        return cls._providers[name.lower()]

# Auto-register default providers
ProviderRegistry.register_provider(OpenAIAdapter())
ProviderRegistry.register_provider(GeminiAdapter())
ProviderRegistry.register_provider(GroqAdapter())
ProviderRegistry.register_provider(OllamaAdapter())
