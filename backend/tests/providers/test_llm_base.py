"""
Unit tests for base LLM provider classes.
"""

import pytest
from datetime import datetime

from apps.providers.llm.base import (
    LLMMessage,
    LLMUsage,
    LLMResponse,
    BaseLLMProvider,
)


class TestLLMMessage:
    """Tests for LLMMessage dataclass."""

    def test_create_message(self):
        """Create a basic message."""
        msg = LLMMessage(role='user', content='Hello')
        assert msg.role == 'user'
        assert msg.content == 'Hello'

    def test_to_dict(self):
        """Convert message to dictionary."""
        msg = LLMMessage(role='assistant', content='Hi there!')
        result = msg.to_dict()
        assert result == {'role': 'assistant', 'content': 'Hi there!'}

    def test_system_message(self):
        """Create system message."""
        msg = LLMMessage(role='system', content='You are helpful.')
        assert msg.role == 'system'
        assert msg.to_dict()['role'] == 'system'


class TestLLMUsage:
    """Tests for LLMUsage dataclass."""

    def test_default_values(self):
        """Usage defaults to zeros."""
        usage = LLMUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_with_values(self):
        """Usage with custom values."""
        usage = LLMUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_create_response(self):
        """Create a basic response."""
        response = LLMResponse(
            content='Hello!',
            model='test-model'
        )
        assert response.content == 'Hello!'
        assert response.model == 'test-model'
        assert response.finish_reason == 'stop'
        assert response.is_partial is False

    def test_response_with_usage(self):
        """Response with usage statistics."""
        usage = LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        response = LLMResponse(
            content='Test',
            model='test-model',
            usage=usage
        )
        assert response.usage.total_tokens == 15

    def test_to_dict(self):
        """Convert response to dictionary."""
        usage = LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        response = LLMResponse(
            content='Test response',
            model='claude-3-opus',
            usage=usage,
            finish_reason='stop'
        )
        result = response.to_dict()

        assert result['content'] == 'Test response'
        assert result['model'] == 'claude-3-opus'
        assert result['finish_reason'] == 'stop'
        assert result['usage']['prompt_tokens'] == 10
        assert result['usage']['completion_tokens'] == 5
        assert result['usage']['total_tokens'] == 15
        assert 'created_at' in result

    def test_streaming_response(self):
        """Response marked as partial for streaming."""
        response = LLMResponse(
            content='Hello',
            model='test-model',
            is_partial=True
        )
        assert response.is_partial is True


class ConcreteTestProvider(BaseLLMProvider):
    """Concrete implementation for testing abstract base class."""

    @property
    def name(self) -> str:
        return 'test'

    def generate(self, messages, model, **kwargs):
        return LLMResponse(content='generated', model=model)

    async def generate_async(self, messages, model, **kwargs):
        return LLMResponse(content='generated async', model=model)

    async def stream(self, messages, model, **kwargs):
        yield LLMResponse(content='chunk1', model=model, is_partial=True)
        yield LLMResponse(content='chunk2', model=model, is_partial=False)

    def list_models(self):
        return ['model-1', 'model-2']

    def health_check(self):
        return True


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider abstract class."""

    def test_init_with_config(self):
        """Initialize provider with config."""
        config = {'api_key': 'test', 'base_url': 'http://localhost'}
        provider = ConcreteTestProvider(config)
        assert provider.config == config

    def test_prepare_messages_with_system(self):
        """Prepare messages adds system prompt."""
        provider = ConcreteTestProvider({})
        messages = [
            LLMMessage(role='user', content='Hello')
        ]

        result = provider.prepare_messages(messages, 'Be helpful.')

        assert len(result) == 2
        assert result[0].role == 'system'
        assert result[0].content == 'Be helpful.'
        assert result[1].role == 'user'

    def test_prepare_messages_replaces_system(self):
        """Prepare messages replaces existing system prompt."""
        provider = ConcreteTestProvider({})
        messages = [
            LLMMessage(role='system', content='Old prompt'),
            LLMMessage(role='user', content='Hello'),
        ]

        result = provider.prepare_messages(messages, 'New prompt.')

        assert len(result) == 2
        assert result[0].role == 'system'
        assert result[0].content == 'New prompt.'

    def test_prepare_messages_without_system(self):
        """Prepare messages without adding system prompt."""
        provider = ConcreteTestProvider({})
        messages = [
            LLMMessage(role='user', content='Hello')
        ]

        result = provider.prepare_messages(messages)

        assert len(result) == 1
        assert result[0].role == 'user'

    def test_inject_variables_single(self):
        """Inject a single variable."""
        provider = ConcreteTestProvider({})
        text = 'Hello, %NAME%!'
        result = provider.inject_variables(text, {'name': 'World'})
        assert result == 'Hello, World!'

    def test_inject_variables_multiple(self):
        """Inject multiple variables."""
        provider = ConcreteTestProvider({})
        text = 'User: %USERNAME% - Role: %ROLE%'
        result = provider.inject_variables(text, {
            'username': 'john',
            'role': 'admin'
        })
        assert result == 'User: john - Role: admin'

    def test_inject_variables_case_insensitive_key(self):
        """Variable names are case-insensitive in keys."""
        provider = ConcreteTestProvider({})
        text = 'Value: %KEY%'
        result = provider.inject_variables(text, {'KEY': 'value1'})
        assert result == 'Value: value1'

    def test_inject_variables_missing(self):
        """Missing variables remain unchanged."""
        provider = ConcreteTestProvider({})
        text = 'Hello, %UNKNOWN%!'
        result = provider.inject_variables(text, {})
        assert result == 'Hello, %UNKNOWN%!'
