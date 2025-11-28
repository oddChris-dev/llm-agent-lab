"""
Queue models for LLM Agent Lab.
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseModel


class QueueStrategy(models.TextChoices):
    FIFO = 'fifo', 'First In, First Out'
    LIFO = 'lifo', 'Last In, First Out'
    ROUND_ROBIN = 'round_robin', 'Round Robin'
    BROADCAST = 'broadcast', 'Broadcast'
    PRIORITY = 'priority', 'Priority Queue'
    CONDITIONAL = 'conditional', 'Conditional Routing'


class QueueItemStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    EXPIRED = 'expired', 'Expired'


class Queue(BaseModel):
    """
    A queue for managing data flow between nodes.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, default='')

    strategy = models.CharField(
        max_length=20,
        choices=QueueStrategy.choices,
        default=QueueStrategy.FIFO
    )
    config = models.JSONField(default=dict, blank=True)

    max_size = models.IntegerField(null=True, blank=True)
    item_ttl_seconds = models.IntegerField(null=True, blank=True)

    # Association
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='queues'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='queues'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class QueueItem(BaseModel):
    """
    An item in a queue.
    """
    queue = models.ForeignKey(
        Queue,
        on_delete=models.CASCADE,
        related_name='items'
    )

    data = models.JSONField()
    priority = models.IntegerField(default=0, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=QueueItemStatus.choices,
        default=QueueItemStatus.PENDING,
        db_index=True
    )

    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    last_error = models.TextField(blank=True, default='')

    available_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Provenance
    source_execution_id = models.UUIDField(null=True, blank=True)
    source_node_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['queue', 'status', 'available_at']),
            models.Index(fields=['queue', 'priority', 'created_at']),
        ]
