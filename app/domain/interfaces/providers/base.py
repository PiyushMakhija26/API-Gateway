from abc import ABC, abstractmethod
from typing import Dict, Any

class AIGatewayProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
        
    @abstractmethod
    def normalize_request(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard gateway request to provider-specific request"""
        pass
        
    @abstractmethod
    def normalize_response(self, response_body: Dict[str, Any]) -> Dict[str, Any]:
        """Convert provider-specific response to standard gateway response"""
        pass
