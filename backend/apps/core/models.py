"""
Base models for LLM Agent Lab.

These models provide common functionality like timestamps and soft delete.
"""

import uuid
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base model with UUID primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """
    Manager that filters out soft-deleted objects by default.
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """Include soft-deleted objects in queryset."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """
    Abstract base model with soft delete functionality.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Manager that includes deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete: set deleted_at timestamp instead of removing."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete the object from the database."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class BaseModel(UUIDModel, TimeStampedModel):
    """
    Standard base model with UUID and timestamps.
    """
    class Meta:
        abstract = True


class BaseSoftDeleteModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Standard base model with UUID, timestamps, and soft delete.
    """
    class Meta:
        abstract = True
