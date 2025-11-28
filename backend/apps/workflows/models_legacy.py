"""
Legacy-compatible models for LLM Agent Lab.

These models maintain backward compatibility with the existing Flask/MySQL system
while integrating with the new workflow architecture.

Mapping:
- Agent → Agent model (legacy prompts, can be converted to LLM node templates)
- Voice → Asset with type='voice_sample'
- Game → Workflow with is_template=True
- Session → Execution
- SessionPlayer → Part of workflow execution context
- SessionHistory → ExecutionLog
- SessionTranscript → NodeExecution output
- Page → WebPage model
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseModel, BaseSoftDeleteModel


class Agent(BaseModel):
    """
    An Agent represents a reusable AI persona with a specific prompt and voice.

    In the new architecture, Agents can be:
    1. Used directly in workflows as LLM node configurations
    2. Converted to workflow templates

    Legacy mapping: agents table
    """
    name = models.CharField(max_length=200, unique=True)
    prompt = models.TextField(
        help_text="System prompt template. Supports variables: %SETTINGS%, %AGENTS%, %PAGES%, etc."
    )
    voice = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agents',
        help_text="Voice sample for TTS output"
    )
    role = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Agent role identifier (e.g., 'brainstorm', 'summary', 'host')"
    )

    # Ownership
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agents'
    )

    # New architecture fields
    default_model = models.CharField(
        max_length=100,
        default='llama3.1:8b',
        help_text="Default LLM model to use"
    )
    default_temperature = models.FloatField(default=0.7)
    default_max_tokens = models.IntegerField(default=512)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def to_node_config(self):
        """Convert agent to LLM node configuration."""
        return {
            'system_prompt': self.prompt,
            'model': self.default_model,
            'temperature': self.default_temperature,
            'max_tokens': self.default_max_tokens,
            'voice_id': str(self.voice_id) if self.voice_id else None,
        }


class GameTemplate(BaseModel):
    """
    A Game template defines a reusable session configuration.

    In the new architecture, GameTemplates are converted to Workflow templates
    with specific agent configurations.

    Legacy mapping: games + game_variables tables
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, default='')
    rules = models.TextField(
        help_text="Game rules and instructions for the orchestration"
    )
    variables = models.JSONField(
        default=dict,
        help_text="Default variables for sessions (e.g., topic, depth)"
    )

    # Link to new workflow
    workflow = models.OneToOneField(
        'workflows.Workflow',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='game_template',
        help_text="Generated workflow template for this game"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='game_templates'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class GamePlayer(BaseModel):
    """
    Defines an agent's role in a game template.

    Legacy mapping: session_players (as template, not instance)
    """
    game = models.ForeignKey(
        GameTemplate,
        on_delete=models.CASCADE,
        related_name='players'
    )
    turn_order = models.PositiveIntegerField()
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='game_roles'
    )
    voice = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Override voice for this role"
    )

    class Meta:
        ordering = ['turn_order']
        unique_together = [['game', 'turn_order']]

    def __str__(self):
        return f"{self.game.name} - Turn {self.turn_order}: {self.agent.name}"


class WebPage(BaseModel):
    """
    Stores fetched web pages with their content and metadata.

    Used by the browser watcher and web search features.

    Legacy mapping: pages table
    """
    execution = models.ForeignKey(
        'executions.Execution',
        on_delete=models.CASCADE,
        related_name='pages'
    )

    # URL info
    url = models.URLField(max_length=2000)
    url_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of URL for fast lookups"
    )

    # Content
    title = models.CharField(max_length=500, blank=True, default='')
    body = models.TextField(blank=True, default='')
    summary = models.TextField(blank=True, default='')

    # Relationships
    parent_url_hash = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
        help_text="Hash of parent URL (the page this was linked from)"
    )

    # Search info
    search_term = models.CharField(max_length=500, blank=True, default='')
    search_rank = models.PositiveIntegerField(null=True, blank=True)

    # Timestamps
    last_loaded = models.DateTimeField(null=True, blank=True)
    last_opened = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [['execution', 'url_hash']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['execution', 'parent_url_hash']),
            models.Index(fields=['execution', 'search_term']),
        ]

    def __str__(self):
        return self.title or self.url[:50]

    def save(self, *args, **kwargs):
        import hashlib
        if not self.url_hash:
            self.url_hash = hashlib.sha256(self.url.encode()).hexdigest()
        super().save(*args, **kwargs)

    @property
    def has_body(self):
        return bool(self.body)

    @property
    def has_summary(self):
        return bool(self.summary)


class Transcript(BaseModel):
    """
    Stores generated transcripts/outputs from agent execution.

    Used for radio show segments, generated content, etc.

    Legacy mapping: transcripts table
    """
    execution = models.ForeignKey(
        'executions.Execution',
        on_delete=models.CASCADE,
        related_name='transcripts'
    )

    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transcripts'
    )

    # Content
    content = models.TextField()
    url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text="Associated URL if content is about a web page"
    )

    # Audio output
    audio_asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transcripts',
        help_text="Generated audio file"
    )

    # Playback status
    played_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agent.name if self.agent else 'Unknown'}: {self.content[:50]}..."
