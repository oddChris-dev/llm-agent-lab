"""
Unit tests for Ollama LLM provider.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from apps.providers.llm.ollama import OllamaProvider
from apps.providers.llm.base import LLMMessage, LLMUsage


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    def test_init_defaults(self):
        """Initialize with default configuration."""
        provider = OllamaProvider()
        assert provider.name == 'ollama'
        assert provider.base_url == 'http://localhost:11434'
        assert provider.timeout == 120.0
        assert provider.keep_alive == '5m'

    def test_init_custom_config(self):
        """Initialize with custom configuration."""
        config = {
            'base_url': 'http://custom:8080/',
            'timeout': 60,
            'keep_alive': '10m'
        }
        provider = OllamaProvider(config)
        assert provider.base_url == 'http://custom:8080'  # Trailing slash stripped
        assert provider.timeout == 60
        assert provider.keep_alive == '10m'

    def test_build_payload_basic(self):
        """Build basic request payload."""
        provider = OllamaProvider()
        messages = [LLMMessage(role='user', content='Hello')]

        payload = provider._build_payload(
            messages=messages,
            model='llama3.1:8b',
            temperature=0.7,
            max_tokens=1024,
            stop=None
        )

        assert payload['model'] == 'llama3.1:8b'
        assert payload['messages'] == [{'role': 'user', 'content': 'Hello'}]
        assert payload['options']['temperature'] == 0.7
        assert payload['options']['num_predict'] == 1024
        assert payload['keep_alive'] == '5m'

    def test_build_payload_with_stop(self):
        """Build payload with stop sequences."""
        provider = OllamaProvider()
        messages = [LLMMessage(role='user', content='Test')]

        payload = provider._build_payload(
            messages=messages,
            model='llama3.1',
            temperature=0.5,
            max_tokens=512,
            stop=['END', 'STOP']
        )

        assert payload['options']['stop'] == ['END', 'STOP']

    def test_build_payload_with_extra_options(self):
        """Build payload with additional options."""
        provider = OllamaProvider()
        messages = [LLMMessage(role='user', content='Test')]

        payload = provider._build_payload(
            messages=messages,
            model='mistral',
            temperature=0.7,
            max_tokens=1024,
            stop=None,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            seed=42
        )

        assert payload['options']['top_p'] == 0.9
        assert payload['options']['top_k'] == 40
        assert payload['options']['repeat_penalty'] == 1.1
        assert payload['options']['seed'] == 42

    def test_parse_response(self):
        """Parse Ollama API response."""
        provider = OllamaProvider()

        api_response = {
            'message': {'content': 'Hello there!'},
            'prompt_eval_count': 10,
            'eval_count': 5
        }

        result = provider._parse_response(api_response, 'llama3.1')

        assert result.content == 'Hello there!'
        assert result.model == 'llama3.1'
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 5
        assert result.usage.total_tokens == 15
        assert result.finish_reason == 'stop'

    def test_parse_response_empty_content(self):
        """Parse response with no content."""
        provider = OllamaProvider()

        api_response = {
            'message': {},
            'prompt_eval_count': 0,
            'eval_count': 0
        }

        result = provider._parse_response(api_response, 'mistral')

        assert result.content == ''
        assert result.usage.total_tokens == 0

    @patch('httpx.Client')
    def test_generate_success(self, mock_client_class):
        """Generate response successfully."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {'content': 'Response text'},
            'prompt_eval_count': 15,
            'eval_count': 10
        }
        mock_client.post.return_value = mock_response

        provider = OllamaProvider()
        messages = [LLMMessage(role='user', content='Hello')]

        result = provider.generate(messages, 'llama3.1')

        assert result.content == 'Response text'
        mock_client.post.assert_called_once()

    @patch('httpx.Client')
    def test_list_models(self, mock_client_class):
        """List available models."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.1:8b'},
                {'name': 'mistral:7b'},
                {'name': 'codellama:13b'}
            ]
        }
        mock_client.get.return_value = mock_response

        provider = OllamaProvider()
        models = provider.list_models()

        assert 'codellama:13b' in models
        assert 'llama3.1:8b' in models
        assert 'mistral:7b' in models
        assert models == sorted(models)  # Should be sorted

    @patch('httpx.Client')
    def test_health_check_success(self, mock_client_class):
        """Health check returns true when server responds."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        provider = OllamaProvider()
        assert provider.health_check() is True

    @patch('httpx.Client')
    def test_health_check_failure(self, mock_client_class):
        """Health check returns false on error."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)
        mock_client.get.side_effect = httpx.ConnectError('Connection refused')

        provider = OllamaProvider()
        assert provider.health_check() is False

    @patch('httpx.Client')
    def test_pull_model_success(self, mock_client_class):
        """Pull model returns true on success."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response

        provider = OllamaProvider()
        result = provider.pull_model('llama3.1:8b')

        assert result is True
        mock_client.post.assert_called_with(
            'http://localhost:11434/api/pull',
            json={'name': 'llama3.1:8b', 'stream': False}
        )

    @patch('httpx.Client')
    def test_get_model_info(self, mock_client_class):
        """Get detailed model information."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = Mock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'modelfile': 'FROM llama3.1',
            'parameters': 'temperature 0.7',
            'template': '{{ .Prompt }}'
        }
        mock_client.post.return_value = mock_response

        provider = OllamaProvider()
        info = provider.get_model_info('llama3.1')

        assert 'modelfile' in info
        assert 'parameters' in info


@pytest.mark.asyncio
class TestOllamaProviderAsync:
    """Async tests for OllamaProvider."""

    @patch('httpx.AsyncClient')
    async def test_generate_async_success(self, mock_client_class):
        """Generate response asynchronously."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {'content': 'Async response'},
            'prompt_eval_count': 20,
            'eval_count': 15
        }
        mock_client.post = AsyncMock(return_value=mock_response)

        provider = OllamaProvider()
        messages = [LLMMessage(role='user', content='Test')]

        result = await provider.generate_async(messages, 'llama3.1')

        assert result.content == 'Async response'
        assert result.usage.total_tokens == 35
