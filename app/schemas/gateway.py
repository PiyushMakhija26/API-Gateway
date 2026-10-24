from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ChatCompletionRequest(BaseModel):
    """OpenAI-style chat request. Unknown fields (temperature, max_tokens, ...)
    are passed through to the upstream provider untouched."""
    model_config = ConfigDict(extra="allow")

    provider: Optional[str] = None  # omit to let the gateway pick and fail over
    model: str
    messages: List[Dict[str, Any]]
    stream: bool = False
