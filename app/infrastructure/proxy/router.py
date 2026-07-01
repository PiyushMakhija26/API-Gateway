from typing import Dict, Any, List
from app.domain.entities.route import Route
from app.domain.entities.provider import Provider
from app.infrastructure.proxy.provider_registry import ProviderRegistry
from app.infrastructure.proxy.proxy_engine import ProxyEngine
from app.infrastructure.proxy.load_balancer import RoundRobinLoadBalancer

class GatewayRouter:
    def __init__(self, proxy_engine: ProxyEngine):
        self.proxy_engine = proxy_engine
        
    async def route_request(
        self,
        route: Route,
        provider: Provider,
        api_keys: List[str], 
        request_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        adapter = ProviderRegistry.get_provider(provider.name.lower())
        
        # Load balance across available API keys for this provider
        if api_keys:
            lb = RoundRobinLoadBalancer(api_keys)
            selected_key = lb.get_next()
        else:
            selected_key = ""
            
        response = await self.proxy_engine.forward_request(
            provider=adapter,
            base_url=provider.base_url,
            api_key=selected_key,
            request_body=request_body,
            timeout=route.timeout_seconds
        )
        
        return response
