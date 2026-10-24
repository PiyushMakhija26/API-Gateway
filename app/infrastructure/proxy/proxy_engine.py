import httpx
from typing import Dict, Any
from app.domain.interfaces.providers.base import AIGatewayProvider
from app.core.exceptions import UpstreamProviderException

class ProxyEngine:
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def forward_request(
        self,
        provider: AIGatewayProvider,
        base_url: str,
        api_key: str,
        request_body: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:

        normalized_body = provider.normalize_request(request_body)

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = await self.http_client.post(
                url=base_url,
                json=normalized_body,
                headers=headers,
                timeout=timeout
            )
            response.raise_for_status()

            return provider.normalize_response(response.json())

        except httpx.HTTPStatusError as e:
            raise UpstreamProviderException(
                f"Provider {provider.provider_name} returned error: {e.response.text[:500]}",
                status_code=e.response.status_code
            )
        except httpx.TimeoutException:
            raise UpstreamProviderException(f"Provider {provider.provider_name} timed out", status_code=504)
        except httpx.RequestError as e:
            raise UpstreamProviderException(f"Failed to connect to provider {provider.provider_name}: {str(e)}")
        except ValueError:
            raise UpstreamProviderException(f"Provider {provider.provider_name} returned a non-JSON response")
