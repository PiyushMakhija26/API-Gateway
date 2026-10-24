from typing import Dict, Any
from app.domain.interfaces.providers.base import AIGatewayProvider

class OllamaAdapter(AIGatewayProvider):
    @property
    def provider_name(self) -> str:
        return "ollama"

    def normalize_request(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        return request_body

    def normalize_response(self, response_body: Dict[str, Any]) -> Dict[str, Any]:
        return response_body
