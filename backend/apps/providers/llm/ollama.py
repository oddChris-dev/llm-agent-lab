"""
Ollama LLM Provider.

Provides integration with Ollama for running local LLM models.
Supports models like Llama, Mistral, Phi, Qwen, and more.
"""

import httpx
import json
from typing import List, Optional, AsyncIterator
from datetime import datetime

from .base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.

    Config options:
        base_url: Ollama API URL (default: http://localhost:11434)
        timeout: Request timeout in seconds (default: 120)
        keep_alive: How long to keep model loaded (default: "5m")
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_TIMEOUT = 120.0

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.base_url = self.config.get('base_url', self.DEFAULT_BASE_URL).rstrip('/')
        self.timeout = self.config.get('timeout', self.DEFAULT_TIMEOUT)
        self.keep_alive = self.config.get('keep_alive', '5m')

    @property
    def name(self) -> str:
        return 'ollama'

    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response synchronously using Ollama."""

        payload = self._build_payload(
            messages, model, temperature, max_tokens, stop, **kwargs
        )
        payload['stream'] = False

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, model)

    async def generate_async(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response asynchronously using Ollama."""

        payload = self._build_payload(
            messages, model, temperature, max_tokens, stop, **kwargs
        )
        payload['stream'] = False

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, model)

    async def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """Stream response tokens from Ollama."""

        payload = self._build_payload(
            messages, model, temperature, max_tokens, stop, **kwargs
        )
        payload['stream'] = True

        accumulated_content = ""

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                'POST',
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message = data.get('message', {})
                    content = message.get('content', '')
                    accumulated_content += content

                    is_done = data.get('done', False)

                    # Parse usage if available (on final message)
                    usage = LLMUsage()
                    if is_done:
                        usage = LLMUsage(
                            prompt_tokens=data.get('prompt_eval_count', 0),
                            completion_tokens=data.get('eval_count', 0),
                            total_tokens=(
                                data.get('prompt_eval_count', 0) +
                                data.get('eval_count', 0)
                            )
                        )

                    yield LLMResponse(
                        content=content,
                        model=model,
                        usage=usage,
                        finish_reason='stop' if is_done else 'length',
                        is_partial=not is_done,
                    )

    def list_models(self) -> List[str]:
        """List available Ollama models."""

        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

        models = []
        for model_info in data.get('models', []):
            models.append(model_info.get('name', ''))

        return sorted(models)

    def health_check(self) -> bool:
        """Check if Ollama is available."""

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    def pull_model(self, model: str) -> bool:
        """
        Pull a model from Ollama registry.

        Args:
            model: Model name to pull (e.g., 'llama3.1:8b')

        Returns:
            True if pull was successful
        """
        try:
            with httpx.Client(timeout=600.0) as client:
                response = client.post(
                    f"{self.base_url}/api/pull",
                    json={'name': model, 'stream': False}
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self, model: str) -> dict:
        """Get detailed information about a model."""

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/api/show",
                json={'name': model}
            )
            response.raise_for_status()
            return response.json()

    def _build_payload(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float,
        max_tokens: int,
        stop: Optional[List[str]],
        **kwargs
    ) -> dict:
        """Build the request payload for Ollama API."""

        payload = {
            'model': model,
            'messages': [msg.to_dict() for msg in messages],
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
            },
            'keep_alive': self.keep_alive,
        }

        if stop:
            payload['options']['stop'] = stop

        # Add any additional options
        if 'top_p' in kwargs:
            payload['options']['top_p'] = kwargs['top_p']
        if 'top_k' in kwargs:
            payload['options']['top_k'] = kwargs['top_k']
        if 'repeat_penalty' in kwargs:
            payload['options']['repeat_penalty'] = kwargs['repeat_penalty']
        if 'seed' in kwargs:
            payload['options']['seed'] = kwargs['seed']

        return payload

    def _parse_response(self, data: dict, model: str) -> LLMResponse:
        """Parse Ollama API response into LLMResponse."""

        message = data.get('message', {})
        content = message.get('content', '')

        usage = LLMUsage(
            prompt_tokens=data.get('prompt_eval_count', 0),
            completion_tokens=data.get('eval_count', 0),
            total_tokens=(
                data.get('prompt_eval_count', 0) +
                data.get('eval_count', 0)
            )
        )

        return LLMResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason='stop',
            created_at=datetime.utcnow(),
        )
