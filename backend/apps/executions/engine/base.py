"""
Base Workflow Engine interfaces.

Defines the core abstractions for workflow execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, AsyncIterator
from enum import Enum
from datetime import datetime
import asyncio


class NodeStatus(str, Enum):
    """Status of a node during execution."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'
    WAITING = 'waiting'  # Waiting for input or external event


class ExecutionStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class NodeResult:
    """Result of executing a single node."""
    node_id: str
    status: NodeStatus
    output: Any = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'status': self.status.value,
            'output': self.output,
            'error': self.error,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metrics': self.metrics,
        }


@dataclass
class ExecutionContext:
    """
    Context passed through workflow execution.

    Contains all state and configuration for the current execution.
    """
    execution_id: str
    workflow_id: str
    user_id: Optional[str] = None

    # Variables/state that persist across nodes
    variables: Dict[str, Any] = field(default_factory=dict)

    # Node outputs indexed by node_id
    node_outputs: Dict[str, Any] = field(default_factory=dict)

    # Execution history
    history: List[NodeResult] = field(default_factory=list)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Provider instances (LLM, TTS, etc.)
    providers: Dict[str, Any] = field(default_factory=dict)

    # Callbacks for events
    on_node_start: Optional[Callable] = None
    on_node_complete: Optional[Callable] = None
    on_status_change: Optional[Callable] = None

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value."""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any):
        """Set a variable value."""
        self.variables[name] = value

    def get_node_output(self, node_id: str) -> Any:
        """Get output from a specific node."""
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: Any):
        """Set output for a node."""
        self.node_outputs[node_id] = output

    def add_history(self, result: NodeResult):
        """Add a node result to history."""
        self.history.append(result)

    def get_provider(self, provider_type: str) -> Any:
        """Get a provider instance."""
        return self.providers.get(provider_type)

    def substitute_variables(self, text: str) -> str:
        """
        Replace variable placeholders in text.

        Variables are in format %VARIABLE_NAME%
        """
        result = text
        for key, value in self.variables.items():
            placeholder = f'%{key.upper()}%'
            result = result.replace(placeholder, str(value))
        return result


class BaseNodeExecutor(ABC):
    """
    Base class for node executors.

    Each node type has a corresponding executor that handles its execution.
    """

    @property
    @abstractmethod
    def node_type(self) -> str:
        """The node type this executor handles."""
        pass

    @abstractmethod
    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        """
        Execute the node.

        Args:
            node_config: Node configuration from workflow
            inputs: Input values from connected nodes
            context: Execution context

        Returns:
            NodeResult with output and status
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate node configuration.

        Returns list of validation errors, empty if valid.
        """
        return []


class WorkflowEngine(ABC):
    """
    Abstract base class for workflow engines.

    Handles the execution of workflows, managing node traversal,
    data flow, and state management.
    """

    @abstractmethod
    async def execute(
        self,
        workflow_id: str,
        context: ExecutionContext,
        start_node_id: Optional[str] = None
    ) -> ExecutionContext:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute
            context: Execution context
            start_node_id: Optional node to start from

        Returns:
            Updated execution context
        """
        pass

    @abstractmethod
    async def execute_node(
        self,
        node_id: str,
        context: ExecutionContext
    ) -> NodeResult:
        """Execute a single node."""
        pass

    @abstractmethod
    async def pause(self, execution_id: str):
        """Pause a running execution."""
        pass

    @abstractmethod
    async def resume(self, execution_id: str):
        """Resume a paused execution."""
        pass

    @abstractmethod
    async def cancel(self, execution_id: str):
        """Cancel an execution."""
        pass

    @abstractmethod
    def get_status(self, execution_id: str) -> ExecutionStatus:
        """Get execution status."""
        pass


class EventEmitter:
    """Simple event emitter for workflow events."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable):
        """Register event listener."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable):
        """Remove event listener."""
        if event in self._listeners:
            self._listeners[event].remove(callback)

    async def emit(self, event: str, *args, **kwargs):
        """Emit event to all listeners."""
        if event in self._listeners:
            for callback in self._listeners[event]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
