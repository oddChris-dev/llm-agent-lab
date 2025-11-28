"""
Unit tests for Anthropic Claude LLM provider.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
import os

from apps.providers.llm.anthropic import AnthropicProvider
from apps.providers.llm.base import LLMMessage, LLMUsage


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_init_with_api_key(self):
        """Initialize with API key in config."""
        provider = AnthropicProvider({'api_key': 'test-key'})
        assert provider.name == 'anthropic'
        assert provider.api_key == 'test-key'
        assert provider.base_url == 'https://api.anthropic.com'
        assert provider.timeout == 120.0
        assert provider.default_model == 'claude-sonnet-4-20250514'

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-key'})
    def test_init_with_env_api_key(self):
        """Initialize with API key from environment."""
        provider = AnthropicProvider({})
        assert provider.api_key == 'env-key'

    def test_init_without_api_key_raises(self):
        """Initialize without API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove env var if it exists
            os.environ.pop('ANTHROPIC_API_KEY', None)
            with pytest.raises(ValueError, match='API key required'):
                AnthropicProvider({})

    def test_init_custom_config(self):
        """Initialize with custom configuration."""
        config = {
            'api_key': 'custom-key',
            'base_url': 'https://custom.api.com/',
            'timeout': 60,
            'default_model': 'claude-3-opus-20240229'
        }
        provider = AnthropicProvider(config)
        assert provider.base_url == 'https://custom.api.com'
        assert provider.timeout == 60
        assert provider.default_model == 'claude-3-opus-20240229'

    def test_get_headers(self):
        """Get proper headers for API requests."""
        provider = AnthropicProvider({'api_key': 'test-key-123'})
        headers = provider._get_headers()

        assert headers['x-api-key'] == 'test-key-123'
        assert headers['anthropic-version'] == '2023-06-01'
        assert headers['content-type'] == 'application/json'

    def test_build_payload_basic(self):
        """Build basic request payload."""
        provider = AnthropicProvider({'api_key': 'test'})
        messages = [LLMMessage(role='user', content='Hello')]

        payload = provider._build_payload(
            messages=messages,
            model='claude-3-opus-20240229',
            temperature=0.7,
            max_tokens=1024,
            stop=None
        )

        assert payload['model'] == 'claude-3-opus-20240229'
        assert payload['messages'] == [{'role': 'user', 'content': 'Hello'}]
        assert payload['temperature'] == 0.7
        assert payload['max_tokens'] == 1024
        assert 'system' not in payload

    def test_build_payload_with_system_message(self):
        """Build payload extracts system message."""
        provider = AnthropicProvider({'api_key': 'test'})
        messages = [
            LLMMessage(role='system', content='Be helpful'),
            LLMMessage(role='user', content='Hello')
        ]

        payload = provider._build_payload(
            messages=messages,
            model='claude-3-opus-20240229',
            temperature=0.5,
            max_tokens=512,
            stop=None
        )

        assert payload['system'] == 'Be helpful'
        assert payload['messages'] == [{'role': 'user', 'content': 'Hello'}]

    def test_build_payload_with_stop_sequences(self):
        """Build payload with stop sequences."""
        provider = AnthropicProvider({'api_key': 'test'})
        messages = [LLMMessage(role='user', content='Test')]

        payload = provider._build_payload(
            messages=messages,
            model='claude-3-sonnet-20240229',
            temperature=0.7,
            max_tokens=1024,
            stop=['END', '\n\nHuman:']
        )

        assert payload['stop_sequences'] == ['END', '\n\nHuman:']

    def test_build_payload_with_extra_options(self):
        """Build payload with additional options."""
        provider = AnthropicProvider({'api_key': 'test'})
        messages = [LLMMessage(role='user', content='Test')]

        payload = provider._build_payload(
            messages=messages,
            model='claude-3-opus-20240229',
            temperature=0.7,
            max_tokens=1024,
            stop=None,
            top_p=0.9,
            top_k=40,
            metadata={'user_id': '123'}
        )

        assert payload['top_p'] == 0.9
        assert payload['top_k'] == 40
        assert payload['metadata'] == {'user_id': '123'}

    def test_parse_response(self):
        """Parse Anthropic API response."""
        provider = AnthropicProvider({'api_key': 'test'})

        api_response = {
            'id': 'msg_123',
            'type': 'message',
            'role': 'assistant',
            'model': 'claude-3-opus-20240229',
            'content': [
                {'type': 'text', 'text': 'Hello! '},
                {'type': 'text', 'text': 'How can I help?'}
            ],
            'stop_reason': 'end_turn',
            'usage': {
                'input_tokens': 15,
                'output_tokens': 10
            }
        }

        result = provider._parse_response(api_response)

        assert result.content == 'Hello! How can I help?'
        assert result.model == 'claude-3-opus-20240229'
        assert result.finish_reason == 'end_turn'
        assert result.usage.prompt_tokens == 15
        assert result.usage.completion_tokens == 10
        assert result.usage.total_tokens == 25

    def test_parse_response_empty_content(self):
        """Parse response with empty content."""
        provider = AnthropicProvider({'api_key': 'test'})

        api_response = {
            'model': 'claude-3-haiku-20240307',
            'content': [],
            'stop_reason': 'stop',
            'usage': {'input_tokens': 0, 'output_tokens': 0}
        }

        result = provider._parse_response(api_response)

        assert result.content == ''
        assert result.usage.total_tokens == 0

    def test_list_models(self):
        """List available models returns predefined list."""
        provider = AnthropicProvider({'api_key': 'test'})
        models = provider.list_models()

        assert 'claude-sonnet-4-20250514' in models
        assert 'claude-3-opus-20240229' in models
        assert 'claude-3-5-sonnet-20241022' in models
        assert len(models) >= 6

    @patch('httpx.Client')
    def test_generate_success(self, mock_client_class):
        """Generate response successfully."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'model': 'claude-3-opus-20240229',
            'content': [{'type': 'text', 'text': 'Response text'}],
            'stop_reason': 'end_turn',
            'usage': {'input_tokens': 10, 'output_tokens': 5}
        }
        mock_client.post.return_value = mock_response

        provider = AnthropicProvider({'api_key': 'test-key'})
        messages = [LLMMessage(role='user', content='Hello')]

        result = provider.generate(messages, 'claude-3-opus-20240229')

        assert result.content == 'Response text'
        mock_client.post.assert_called_once()

        # Verify headers were passed
        call_kwargs = mock_client.post.call_args[1]
        assert 'x-api-key' in call_kwargs['headers']

    @patch('httpx.Client')
    def test_generate_uses_default_model(self, mock_client_class):
        """Generate uses default model when none specified."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'model': 'claude-sonnet-4-20250514',
            'content': [{'type': 'text', 'text': 'Test'}],
            'stop_reason': 'stop',
            'usage': {'input_tokens': 5, 'output_tokens': 2}
        }
        mock_client.post.return_value = mock_response

        provider = AnthropicProvider({'api_key': 'test'})
        messages = [LLMMessage(role='user', content='Test')]

        provider.generate(messages)  # No model specified

        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs['json']['model'] == 'claude-sonnet-4-20250514'

    @patch('httpx.Client')
    def test_health_check_success(self, mock_client_class):
        """Health check returns true on success."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response

        provider = AnthropicProvider({'api_key': 'test-key'})
        assert provider.health_check() is True

    @patch('httpx.Client')
    def test_health_check_auth_error_still_reachable(self, mock_client_class):
        """Health check returns true even with auth error (API reachable)."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response

        provider = AnthropicProvider({'api_key': 'invalid-key'})
        assert provider.health_check() is True

    @patch('httpx.Client')
    def test_health_check_failure(self, mock_client_class):
        """Health check returns false on network error."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)
        mock_client.post.side_effect = httpx.ConnectError('Connection refused')

        provider = AnthropicProvider({'api_key': 'test-key'})
        assert provider.health_check() is False


@pytest.mark.asyncio
class TestAnthropicProviderAsync:
    """Async tests for AnthropicProvider."""

    @patch('httpx.AsyncClient')
    async def test_generate_async_success(self, mock_client_class):
        """Generate response asynchronously."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'model': 'claude-3-opus-20240229',
            'content': [{'type': 'text', 'text': 'Async response'}],
            'stop_reason': 'end_turn',
            'usage': {'input_tokens': 20, 'output_tokens': 10}
        }
        mock_client.post = AsyncMock(return_value=mock_response)

        provider = AnthropicProvider({'api_key': 'test-key'})
        messages = [LLMMessage(role='user', content='Test')]

        result = await provider.generate_async(messages, 'claude-3-opus-20240229')

        assert result.content == 'Async response'
        assert result.usage.total_tokens == 30
