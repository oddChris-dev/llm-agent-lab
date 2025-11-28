"""
Anthropic Claude LLM Provider.

Provides integration with Anthropic's Claude models via their API.
"""

import os
import json
from typing import List, Optional, AsyncIterator
from datetime import datetime

import httpx

from .base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    LLMUsage,
)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude provider for cloud-based LLM inference.

    Config options:
        api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        base_url: API base URL (default: https://api.anthropic.com)
        timeout: Request timeout in seconds (default: 120)
        default_model: Default model to use (default: claude-sonnet-4-20250514)
    """

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_TIMEOUT = 120.0
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    API_VERSION = "2023-06-01"

    # Available Claude models
    MODELS = [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.api_key = self.config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        self.base_url = self.config.get('base_url', self.DEFAULT_BASE_URL).rstrip('/')
        self.timeout = self.config.get('timeout', self.DEFAULT_TIMEOUT)
        self.default_model = self.config.get('default_model', self.DEFAULT_MODEL)

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. "
                "Set via config['api_key'] or ANTHROPIC_API_KEY environment variable."
            )

    @property
    def name(self) -> str:
        return 'anthropic'

    def _get_headers(self) -> dict:
        """Get headers for Anthropic API requests."""
        return {
            'x-api-key': self.api_key,
            'anthropic-version': self.API_VERSION,
            'content-type': 'application/json',
        }

    def generate(
        self,
        messages: List[LLMMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response synchronously using Claude."""

        model = model or self.default_model
        payload = self._build_payload(
            messages, model, temperature, max_tokens, stop, **kwargs
        )

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/v1/messages",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data)

    async def generate_async(
        self,
        messages: List[LLMMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response asynchronously using Claude."""

        model = model or self.default_model
        payload = self._build_payload(
            messages, model, temperature, max_tokens, stop, **kwargs
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data)

    async def stream(
        self,
        messages: List[LLMMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """Stream response tokens from Claude."""

        model = model or self.default_model
        payload = self._build_payload(
            messages, model, temperature, max_tokens, stop, **kwargs
        )
        payload['stream'] = True

        accumulated_content = ""
        input_tokens = 0
        output_tokens = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                'POST',
                f"{self.base_url}/v1/messages",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or not line.startswith('data: '):
                        continue

                    data_str = line[6:]  # Remove 'data: ' prefix
                    if data_str == '[DONE]':
                        break

                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get('type', '')

                    if event_type == 'message_start':
                        message = event.get('message', {})
                        usage = message.get('usage', {})
                        input_tokens = usage.get('input_tokens', 0)

                    elif event_type == 'content_block_delta':
                        delta = event.get('delta', {})
                        if delta.get('type') == 'text_delta':
                            text = delta.get('text', '')
                            accumulated_content += text

                            yield LLMResponse(
                                content=text,
                                model=model,
                                usage=LLMUsage(
                                    prompt_tokens=input_tokens,
                                    completion_tokens=output_tokens,
                                    total_tokens=input_tokens + output_tokens
                                ),
                                finish_reason='',
                                is_partial=True,
                            )

                    elif event_type == 'message_delta':
                        delta = event.get('delta', {})
                        usage = event.get('usage', {})
                        output_tokens = usage.get('output_tokens', 0)
                        finish_reason = delta.get('stop_reason', 'stop')

                        yield LLMResponse(
                            content='',
                            model=model,
                            usage=LLMUsage(
                                prompt_tokens=input_tokens,
                                completion_tokens=output_tokens,
                                total_tokens=input_tokens + output_tokens
                            ),
                            finish_reason=finish_reason,
                            is_partial=False,
                        )

    def list_models(self) -> List[str]:
        """List available Claude models."""
        return self.MODELS.copy()

    def health_check(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            # Make a minimal API call to verify connectivity
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.base_url}/v1/messages",
                    headers=self._get_headers(),
                    json={
                        'model': self.default_model,
                        'max_tokens': 1,
                        'messages': [{'role': 'user', 'content': 'hi'}]
                    }
                )
                # 200 = success, 401 = auth issue but API reachable
                return response.status_code in (200, 401)
        except Exception:
            return False

    def _build_payload(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float,
        max_tokens: int,
        stop: Optional[List[str]],
        **kwargs
    ) -> dict:
        """Build the request payload for Anthropic API."""

        # Separate system message from conversation
        system_content = None
        conversation_messages = []

        for msg in messages:
            if msg.role == 'system':
                # Anthropic uses a separate system parameter
                system_content = msg.content
            else:
                conversation_messages.append({
                    'role': msg.role,
                    'content': msg.content
                })

        payload = {
            'model': model,
            'messages': conversation_messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
        }

        if system_content:
            payload['system'] = system_content

        if stop:
            payload['stop_sequences'] = stop

        # Add optional parameters
        if 'top_p' in kwargs:
            payload['top_p'] = kwargs['top_p']
        if 'top_k' in kwargs:
            payload['top_k'] = kwargs['top_k']
        if 'metadata' in kwargs:
            payload['metadata'] = kwargs['metadata']

        return payload

    def _parse_response(self, data: dict) -> LLMResponse:
        """Parse Anthropic API response into LLMResponse."""

        # Extract content from response
        content_blocks = data.get('content', [])
        content = ''
        for block in content_blocks:
            if block.get('type') == 'text':
                content += block.get('text', '')

        # Parse usage
        usage_data = data.get('usage', {})
        usage = LLMUsage(
            prompt_tokens=usage_data.get('input_tokens', 0),
            completion_tokens=usage_data.get('output_tokens', 0),
            total_tokens=(
                usage_data.get('input_tokens', 0) +
                usage_data.get('output_tokens', 0)
            )
        )

        return LLMResponse(
            content=content,
            model=data.get('model', ''),
            usage=usage,
            finish_reason=data.get('stop_reason', 'stop'),
            created_at=datetime.utcnow(),
        )
