"""
Base LLM Provider interface.

All LLM providers (Ollama, Anthropic, OpenAI, etc.) implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str  # 'system', 'user', 'assistant'
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {'role': self.role, 'content': self.content}


@dataclass
class LLMUsage:
    """Token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    finish_reason: str = 'stop'
    created_at: datetime = field(default_factory=datetime.utcnow)

    # For streaming
    is_partial: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'model': self.model,
            'usage': {
                'prompt_tokens': self.usage.prompt_tokens,
                'completion_tokens': self.usage.completion_tokens,
                'total_tokens': self.usage.total_tokens,
            },
            'finish_reason': self.finish_reason,
            'created_at': self.created_at.isoformat(),
        }


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implementations must provide:
    - generate(): Synchronous generation
    - generate_async(): Asynchronous generation
    - stream(): Streaming generation
    - list_models(): List available models
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration dict
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'ollama', 'anthropic')."""
        pass

    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response synchronously.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
            **kwargs: Provider-specific options

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_async(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response asynchronously.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> AsyncIterator[LLMResponse]:
        """
        Stream response tokens asynchronously.

        Yields:
            LLMResponse objects with partial content
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """
        List available models.

        Returns:
            List of model identifiers
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider is responding
        """
        pass

    def prepare_messages(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None
    ) -> List[LLMMessage]:
        """
        Prepare messages, optionally adding/replacing system prompt.
        """
        result = []

        # Add or replace system prompt
        if system_prompt:
            result.append(LLMMessage(role='system', content=system_prompt))
            # Skip existing system messages
            for msg in messages:
                if msg.role != 'system':
                    result.append(msg)
        else:
            result = list(messages)

        return result

    def inject_variables(self, text: str, variables: Dict[str, str]) -> str:
        """
        Replace template variables in text.

        Variables are in the format %VARIABLE_NAME%
        """
        result = text
        for key, value in variables.items():
            placeholder = f'%{key.upper()}%'
            result = result.replace(placeholder, str(value))
        return result
