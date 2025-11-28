"""
Workflow models for LLM Agent Lab.

These models represent the core workflow structure:
- Workflow: The container for a workflow definition
- Node: Individual processing units within a workflow
- Connection: Links between node ports
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseSoftDeleteModel, BaseModel


class WorkflowStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    ARCHIVED = 'archived', 'Archived'


class Workflow(BaseSoftDeleteModel):
    """
    A workflow is a directed graph of nodes that process data.

    Workflows can be:
    - Draft: Being edited, not executable
    - Active: Ready for execution
    - Archived: No longer in use but preserved

    Templates are workflows that can be cloned as starting points.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, blank=True, default='')
    color = models.CharField(max_length=20, blank=True, default='')

    status = models.CharField(
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True
    )
    is_template = models.BooleanField(default=False, db_index=True)

    # Canvas state (viewport, selection, etc.)
    canvas_data = models.JSONField(default=dict, blank=True)

    # Workflow settings
    settings = models.JSONField(default=dict, blank=True)

    # Ownership
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workflows'
    )

    # Versioning
    version = models.PositiveIntegerField(default=1)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['is_template']),
        ]

    def __str__(self):
        return self.name

    @property
    def node_count(self):
        return self.nodes.count()

    @property
    def connection_count(self):
        return self.connections.count()

    def duplicate(self, new_name=None, user=None):
        """
        Create a copy of this workflow with all nodes and connections.
        """
        # Clone workflow
        new_workflow = Workflow.objects.create(
            name=new_name or f"Copy of {self.name}",
            description=self.description,
            icon=self.icon,
            color=self.color,
            status=WorkflowStatus.DRAFT,
            is_template=False,
            canvas_data=self.canvas_data.copy(),
            settings=self.settings.copy(),
            user=user or self.user,
            parent=self,
        )

        # Map old node IDs to new nodes
        node_map = {}

        # Clone nodes
        for node in self.nodes.all():
            old_id = node.id
            node.pk = None
            node.id = None
            node.workflow = new_workflow
            node.save()
            node_map[old_id] = node

        # Clone connections with updated node references
        for conn in self.connections.all():
            conn.pk = None
            conn.id = None
            conn.workflow = new_workflow
            conn.source_node = node_map.get(conn.source_node_id)
            conn.target_node = node_map.get(conn.target_node_id)
            if conn.source_node and conn.target_node:
                conn.save()

        return new_workflow


class Node(BaseModel):
    """
    A node is a processing unit within a workflow.

    Each node has:
    - A type that defines its behavior (e.g., 'llm.claude', 'voice.tts')
    - A position on the canvas
    - Configuration specific to its type
    - Input and output ports for connections
    """
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='nodes'
    )

    # Node type (e.g., 'llm.claude', 'voice.tts', 'queue.fifo')
    type = models.CharField(max_length=100, db_index=True)

    # Display name (optional, falls back to type's display name)
    name = models.CharField(max_length=200, blank=True, default='')

    # Position on canvas
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)

    # Type-specific configuration
    config = models.JSONField(default=dict, blank=True)

    # Custom input/output overrides
    inputs_config = models.JSONField(default=list, blank=True)
    outputs_config = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name or self.type} ({self.workflow.name})"

    @property
    def position(self):
        return {'x': self.position_x, 'y': self.position_y}

    @position.setter
    def position(self, value):
        self.position_x = value.get('x', 0)
        self.position_y = value.get('y', 0)


class Connection(BaseModel):
    """
    A connection links an output port of one node to an input port of another.

    Connections define the data flow through the workflow.
    """
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='connections'
    )

    # Source
    source_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='outgoing_connections'
    )
    source_port = models.CharField(max_length=100)

    # Target
    target_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='incoming_connections'
    )
    target_port = models.CharField(max_length=100)

    # Visual styling
    style = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source_node', 'source_port', 'target_node', 'target_port'],
                name='unique_connection'
            ),
            models.CheckConstraint(
                check=~models.Q(source_node=models.F('target_node')),
                name='no_self_connection'
            ),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.source_node.name}:{self.source_port} -> {self.target_node.name}:{self.target_port}"
