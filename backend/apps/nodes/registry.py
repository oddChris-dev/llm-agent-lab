"""
Node type registry for LLM Agent Lab.

This module provides a central registry for all available node types.
Node types define the behavior, inputs, outputs, and configuration of nodes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable


@dataclass
class Port:
    """
    Defines an input or output port on a node.
    """
    id: str
    type: str  # 'string', 'number', 'boolean', 'object', 'array', 'any'
    label: str = ''
    required: bool = False
    description: str = ''
    default: Any = None


@dataclass
class NodeTypeDefinition:
    """
    Definition of a node type.
    """
    type: str  # e.g., 'llm.claude'
    category: str  # e.g., 'llm', 'voice', 'web', 'queue'
    name: str  # Display name
    description: str = ''
    icon: str = ''
    color: str = ''

    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)

    config_schema: Dict[str, Any] = field(default_factory=dict)

    # The execute function
    execute_fn: Optional[Callable] = None


class NodeTypeRegistry:
    """
    Singleton registry for all node types.
    """
    _instance = None
    _types: Dict[str, NodeTypeDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._types = {}
        return cls._instance

    def register(self, node_type: NodeTypeDefinition):
        """Register a node type."""
        self._types[node_type.type] = node_type

    def get(self, type_id: str) -> Optional[NodeTypeDefinition]:
        """Get a node type by ID."""
        return self._types.get(type_id)

    def list_all(self) -> List[NodeTypeDefinition]:
        """List all registered node types."""
        return list(self._types.values())

    def list_by_category(self, category: str) -> List[NodeTypeDefinition]:
        """List node types by category."""
        return [t for t in self._types.values() if t.category == category]

    def to_dict(self, node_type: NodeTypeDefinition) -> Dict[str, Any]:
        """Convert node type to API response format."""
        return {
            'type': node_type.type,
            'category': node_type.category,
            'name': node_type.name,
            'description': node_type.description,
            'icon': node_type.icon,
            'color': node_type.color,
            'inputs': [
                {
                    'id': p.id,
                    'type': p.type,
                    'label': p.label or p.id,
                    'required': p.required,
                    'description': p.description,
                }
                for p in node_type.inputs
            ],
            'outputs': [
                {
                    'id': p.id,
                    'type': p.type,
                    'label': p.label or p.id,
                    'description': p.description,
                }
                for p in node_type.outputs
            ],
            'config_schema': node_type.config_schema,
        }


# Global registry instance
registry = NodeTypeRegistry()


def register_node(
    type: str,
    category: str,
    name: str,
    description: str = '',
    icon: str = '',
    color: str = '',
    inputs: List[Port] = None,
    outputs: List[Port] = None,
    config_schema: Dict[str, Any] = None,
):
    """
    Decorator to register a node type from its execute function.

    Usage:
        @register_node(
            type='llm.claude',
            category='llm',
            name='Claude',
            inputs=[Port('prompt', 'string', required=True)],
            outputs=[Port('response', 'string')],
        )
        async def execute_claude(inputs, config, context):
            ...
    """
    def decorator(fn):
        node_type = NodeTypeDefinition(
            type=type,
            category=category,
            name=name,
            description=description,
            icon=icon,
            color=color,
            inputs=inputs or [],
            outputs=outputs or [],
            config_schema=config_schema or {},
            execute_fn=fn,
        )
        registry.register(node_type)
        return fn
    return decorator


# Register built-in node types
def _register_builtin_types():
    """Register all built-in node types."""

    # LLM Nodes
    registry.register(NodeTypeDefinition(
        type='llm.claude',
        category='llm',
        name='Claude',
        description='Anthropic Claude language model',
        icon='robot',
        color='#06B6D4',
        inputs=[
            Port('prompt', 'string', 'Prompt', required=True),
            Port('context', 'string', 'Context'),
            Port('images', 'array', 'Images'),
        ],
        outputs=[
            Port('response', 'string', 'Response'),
            Port('usage', 'object', 'Usage'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'provider_id': {'type': 'string'},
                'model': {'type': 'string', 'default': 'claude-3-opus-20240229'},
                'system_prompt': {'type': 'string'},
                'temperature': {'type': 'number', 'minimum': 0, 'maximum': 2, 'default': 0.7},
                'max_tokens': {'type': 'integer', 'default': 4096},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='llm.openai',
        category='llm',
        name='GPT (OpenAI)',
        description='OpenAI GPT models',
        icon='robot',
        color='#10B981',
        inputs=[
            Port('prompt', 'string', 'Prompt', required=True),
            Port('context', 'string', 'Context'),
        ],
        outputs=[
            Port('response', 'string', 'Response'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'provider_id': {'type': 'string'},
                'model': {'type': 'string', 'default': 'gpt-4-turbo'},
                'system_prompt': {'type': 'string'},
                'temperature': {'type': 'number', 'default': 0.7},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='llm.ollama',
        category='llm',
        name='Ollama (Local)',
        description='Local LLM via Ollama',
        icon='robot',
        color='#8B5CF6',
        inputs=[
            Port('prompt', 'string', 'Prompt', required=True),
        ],
        outputs=[
            Port('response', 'string', 'Response'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'model': {'type': 'string', 'default': 'llama3.1:8b'},
                'system_prompt': {'type': 'string'},
                'temperature': {'type': 'number', 'default': 0.7},
            },
        }
    ))

    # Voice Nodes
    registry.register(NodeTypeDefinition(
        type='voice.tts',
        category='voice',
        name='Text to Speech',
        description='Convert text to audio',
        icon='volume-2',
        color='#EC4899',
        inputs=[
            Port('text', 'string', 'Text', required=True),
            Port('voice_id', 'string', 'Voice'),
        ],
        outputs=[
            Port('audio', 'audio', 'Audio'),
            Port('duration', 'number', 'Duration'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'provider': {'type': 'string', 'enum': ['xtts', 'elevenlabs', 'openai']},
                'voice_id': {'type': 'string'},
                'speed': {'type': 'number', 'default': 1.0},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='voice.stt',
        category='voice',
        name='Speech to Text',
        description='Convert audio to text',
        icon='mic',
        color='#EC4899',
        inputs=[
            Port('audio', 'audio', 'Audio', required=True),
        ],
        outputs=[
            Port('text', 'string', 'Text'),
            Port('confidence', 'number', 'Confidence'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'provider': {'type': 'string', 'enum': ['vosk', 'whisper', 'google']},
                'language': {'type': 'string', 'default': 'en'},
            },
        }
    ))

    # Web Nodes
    registry.register(NodeTypeDefinition(
        type='web.browser_watch',
        category='web',
        name='Browser Watcher',
        description='Watch user browser navigation',
        icon='globe',
        color='#14B8A6',
        inputs=[],
        outputs=[
            Port('url', 'string', 'URL'),
            Port('title', 'string', 'Title'),
            Port('content', 'string', 'Content'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'url_patterns': {'type': 'array', 'items': {'type': 'string'}},
                'exclude_patterns': {'type': 'array'},
                'poll_interval': {'type': 'integer', 'default': 5},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='web.search',
        category='web',
        name='Web Search',
        description='Search the web',
        icon='search',
        color='#14B8A6',
        inputs=[
            Port('query', 'string', 'Query', required=True),
        ],
        outputs=[
            Port('results', 'array', 'Results'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'provider': {'type': 'string', 'enum': ['google', 'bing', 'duckduckgo']},
                'max_results': {'type': 'integer', 'default': 10},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='web.fetch',
        category='web',
        name='Fetch Page',
        description='Fetch and parse a web page',
        icon='download',
        color='#14B8A6',
        inputs=[
            Port('url', 'string', 'URL', required=True),
        ],
        outputs=[
            Port('content', 'string', 'Content'),
            Port('title', 'string', 'Title'),
            Port('links', 'array', 'Links'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'timeout': {'type': 'integer', 'default': 30},
                'extract_links': {'type': 'boolean', 'default': True},
            },
        }
    ))

    # Queue Nodes
    registry.register(NodeTypeDefinition(
        type='queue.fifo',
        category='queue',
        name='FIFO Queue',
        description='First-in, first-out queue',
        icon='list',
        color='#EAB308',
        inputs=[
            Port('input', 'any', 'Input'),
        ],
        outputs=[
            Port('output', 'any', 'Output'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'max_size': {'type': 'integer', 'default': 1000},
                'overflow': {'type': 'string', 'enum': ['drop_oldest', 'drop_newest', 'block']},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='queue.round_robin',
        category='queue',
        name='Round Robin',
        description='Distribute items across outputs',
        icon='shuffle',
        color='#EAB308',
        inputs=[
            Port('input', 'any', 'Input'),
        ],
        outputs=[
            Port('output_1', 'any', 'Output 1'),
            Port('output_2', 'any', 'Output 2'),
            Port('output_3', 'any', 'Output 3'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'output_count': {'type': 'integer', 'default': 3},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='queue.broadcast',
        category='queue',
        name='Broadcast',
        description='Send to all outputs',
        icon='radio',
        color='#EAB308',
        inputs=[
            Port('input', 'any', 'Input'),
        ],
        outputs=[
            Port('output_1', 'any', 'Output 1'),
            Port('output_2', 'any', 'Output 2'),
            Port('output_3', 'any', 'Output 3'),
        ],
        config_schema={}
    ))

    # Image Nodes
    registry.register(NodeTypeDefinition(
        type='image.generate',
        category='image',
        name='Generate Image',
        description='Generate image from text',
        icon='image',
        color='#F97316',
        inputs=[
            Port('prompt', 'string', 'Prompt', required=True),
            Port('negative_prompt', 'string', 'Negative Prompt'),
        ],
        outputs=[
            Port('image', 'image', 'Image'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'provider': {'type': 'string', 'enum': ['comfyui', 'automatic1111', 'dalle']},
                'model': {'type': 'string'},
                'width': {'type': 'integer', 'default': 1024},
                'height': {'type': 'integer', 'default': 1024},
                'steps': {'type': 'integer', 'default': 30},
            },
        }
    ))

    # Trigger Nodes
    registry.register(NodeTypeDefinition(
        type='trigger.manual',
        category='trigger',
        name='Manual Trigger',
        description='Manually triggered start',
        icon='play',
        color='#8B5CF6',
        inputs=[],
        outputs=[
            Port('trigger', 'object', 'Trigger Data'),
        ],
        config_schema={}
    ))

    registry.register(NodeTypeDefinition(
        type='trigger.schedule',
        category='trigger',
        name='Schedule',
        description='Trigger on schedule',
        icon='clock',
        color='#8B5CF6',
        inputs=[],
        outputs=[
            Port('trigger', 'object', 'Trigger Data'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'cron': {'type': 'string'},
                'timezone': {'type': 'string', 'default': 'UTC'},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='trigger.webhook',
        category='trigger',
        name='Webhook',
        description='Trigger via HTTP webhook',
        icon='zap',
        color='#8B5CF6',
        inputs=[],
        outputs=[
            Port('payload', 'object', 'Payload'),
            Port('headers', 'object', 'Headers'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'secret': {'type': 'string'},
            },
        }
    ))

    # Control Flow
    registry.register(NodeTypeDefinition(
        type='control.condition',
        category='control',
        name='Condition',
        description='Conditional branching',
        icon='git-branch',
        color='#6366F1',
        inputs=[
            Port('value', 'any', 'Value', required=True),
        ],
        outputs=[
            Port('if_true', 'any', 'If True'),
            Port('if_false', 'any', 'If False'),
        ],
        config_schema={
            'type': 'object',
            'properties': {
                'expression': {'type': 'string'},
            },
        }
    ))

    registry.register(NodeTypeDefinition(
        type='control.loop',
        category='control',
        name='Loop',
        description='Iterate over items',
        icon='repeat',
        color='#6366F1',
        inputs=[
            Port('items', 'array', 'Items', required=True),
        ],
        outputs=[
            Port('item', 'any', 'Current Item'),
            Port('index', 'number', 'Index'),
            Port('done', 'boolean', 'Completed'),
        ],
        config_schema={}
    ))

    # Output Nodes
    registry.register(NodeTypeDefinition(
        type='output.display',
        category='output',
        name='Display',
        description='Show output to user',
        icon='monitor',
        color='#22C55E',
        inputs=[
            Port('content', 'any', 'Content', required=True),
        ],
        outputs=[],
        config_schema={
            'type': 'object',
            'properties': {
                'format': {'type': 'string', 'enum': ['text', 'html', 'markdown']},
            },
        }
    ))


# Initialize built-in types
_register_builtin_types()
