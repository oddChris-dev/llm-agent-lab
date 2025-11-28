"""
Provider models for LLM Agent Lab.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseModel


class ProviderType(models.TextChoices):
    LLM = 'llm', 'Language Model'
    VOICE_TTS = 'voice_tts', 'Text to Speech'
    VOICE_STT = 'voice_stt', 'Speech to Text'
    IMAGE = 'image', 'Image Generation'


class ProviderStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ERROR = 'error', 'Error'


class Provider(BaseModel):
    """
    A provider represents an external service integration.

    Providers store configuration for services like:
    - LLM: Anthropic, OpenAI, Ollama
    - TTS: XTTS, ElevenLabs
    - STT: Vosk, Whisper
    - Image: Stable Diffusion, DALL-E
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=ProviderType.choices, db_index=True)

    # Configuration (API keys stored encrypted)
    config = models.JSONField(default=dict)

    # State
    status = models.CharField(
        max_length=20,
        choices=ProviderStatus.choices,
        default=ProviderStatus.ACTIVE
    )
    is_default = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)  # System providers can't be deleted

    # Ownership (null for system providers)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='providers'
    )

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'type'],
                condition=models.Q(is_default=True),
                name='unique_default_per_type'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
