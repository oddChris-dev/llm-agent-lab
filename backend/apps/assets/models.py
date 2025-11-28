"""
Asset models for LLM Agent Lab.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseSoftDeleteModel


class AssetType(models.TextChoices):
    VOICE_SAMPLE = 'voice_sample', 'Voice Sample'
    IMAGE = 'image', 'Image'
    AUDIO = 'audio', 'Audio'
    VIDEO = 'video', 'Video'
    DOCUMENT = 'document', 'Document'
    OTHER = 'other', 'Other'


class Asset(BaseSoftDeleteModel):
    """
    An asset is a stored file like a voice sample, image, or generated content.
    """
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=AssetType.choices, db_index=True)

    # Storage
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True, default='')
    checksum = models.CharField(max_length=64, blank=True, default='')

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)

    # Ownership
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assets'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
