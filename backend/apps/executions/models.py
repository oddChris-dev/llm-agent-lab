"""
Execution models for LLM Agent Lab.
"""

from django.db import models
from apps.core.models import BaseModel


class ExecutionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    RUNNING = 'running', 'Running'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class NodeExecutionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    QUEUED = 'queued', 'Queued'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    SKIPPED = 'skipped', 'Skipped'


class LogLevel(models.TextChoices):
    DEBUG = 'debug', 'Debug'
    INFO = 'info', 'Info'
    WARNING = 'warning', 'Warning'
    ERROR = 'error', 'Error'


class Execution(BaseModel):
    """
    An execution represents a single run of a workflow.
    """
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        related_name='executions'
    )

    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
        db_index=True
    )

    # Progress
    total_nodes = models.IntegerField(default=0)
    completed_nodes = models.IntegerField(default=0)
    failed_nodes = models.IntegerField(default=0)

    # Context
    context = models.JSONField(default=dict, blank=True)

    # Trigger info
    trigger_type = models.CharField(max_length=50, blank=True, default='')
    trigger_data = models.JSONField(default=dict, blank=True)

    # Error info
    error_message = models.TextField(blank=True, default='')
    error_node_id = models.UUIDField(null=True, blank=True)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Parent execution (for sub-workflows)
    parent_execution = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_executions'
    )
    parent_node_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"Execution {self.id} ({self.status})"


class NodeExecution(BaseModel):
    """
    Tracks the execution of a single node.
    """
    execution = models.ForeignKey(
        Execution,
        on_delete=models.CASCADE,
        related_name='node_executions'
    )
    node = models.ForeignKey(
        'workflows.Node',
        on_delete=models.CASCADE,
        related_name='executions'
    )

    status = models.CharField(
        max_length=20,
        choices=NodeExecutionStatus.choices,
        default=NodeExecutionStatus.PENDING,
        db_index=True
    )

    input_data = models.JSONField(null=True, blank=True)
    output_data = models.JSONField(null=True, blank=True)

    error_message = models.TextField(blank=True, default='')
    error_traceback = models.TextField(blank=True, default='')

    retry_count = models.IntegerField(default=0)

    queued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"NodeExecution {self.node.name} ({self.status})"


class ExecutionLog(models.Model):
    """
    Log entries for execution debugging.
    """
    id = models.BigAutoField(primary_key=True)
    execution = models.ForeignKey(
        Execution,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    node_execution = models.ForeignKey(
        NodeExecution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='logs'
    )

    level = models.CharField(
        max_length=10,
        choices=LogLevel.choices,
        default=LogLevel.INFO
    )
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['execution', 'timestamp']),
        ]
