"""
Workflow Executor.

Main execution engine for node-based workflows.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict

from .base import (
    WorkflowEngine,
    ExecutionContext,
    NodeResult,
    NodeStatus,
    ExecutionStatus,
    BaseNodeExecutor,
    EventEmitter,
)


class WorkflowExecutor(WorkflowEngine):
    """
    Main workflow execution engine.

    Handles DAG traversal, parallel execution, and data flow
    between nodes.
    """

    def __init__(self):
        self._node_executors: Dict[str, BaseNodeExecutor] = {}
        self._executions: Dict[str, ExecutionContext] = {}
        self._status: Dict[str, ExecutionStatus] = {}
        self._events = EventEmitter()
        self._paused: Set[str] = set()
        self._cancelled: Set[str] = set()

    def register_executor(self, executor: BaseNodeExecutor):
        """Register a node executor."""
        self._node_executors[executor.node_type] = executor

    def get_executor(self, node_type: str) -> Optional[BaseNodeExecutor]:
        """Get executor for a node type."""
        return self._node_executors.get(node_type)

    async def execute(
        self,
        workflow_id: str,
        context: ExecutionContext,
        start_node_id: Optional[str] = None
    ) -> ExecutionContext:
        """Execute a workflow."""
        from apps.workflows.models import Workflow, Node, Connection

        # Load workflow
        workflow = await asyncio.to_thread(
            Workflow.objects.get,
            id=workflow_id
        )

        # Load nodes and connections
        nodes = await asyncio.to_thread(
            list,
            Node.objects.filter(workflow=workflow)
        )
        connections = await asyncio.to_thread(
            list,
            Connection.objects.filter(workflow=workflow)
        )

        # Build execution graph
        graph = self._build_graph(nodes, connections)

        # Track execution
        self._executions[context.execution_id] = context
        self._status[context.execution_id] = ExecutionStatus.RUNNING

        await self._events.emit('execution_start', context)

        try:
            # Find start nodes (nodes with no incoming connections)
            if start_node_id:
                start_nodes = [start_node_id]
            else:
                start_nodes = self._find_start_nodes(graph)

            # Execute workflow using topological order
            await self._execute_graph(
                graph,
                nodes,
                start_nodes,
                context
            )

            self._status[context.execution_id] = ExecutionStatus.COMPLETED

        except Exception as e:
            self._status[context.execution_id] = ExecutionStatus.FAILED
            await self._events.emit('execution_error', context, str(e))
            raise

        finally:
            await self._events.emit('execution_complete', context)

        return context

    def _build_graph(
        self,
        nodes: List,
        connections: List
    ) -> Dict[str, Dict]:
        """Build execution graph from nodes and connections."""
        graph = {}

        # Initialize nodes
        for node in nodes:
            graph[str(node.id)] = {
                'node': node,
                'inputs': [],
                'outputs': [],
                'config': node.config or {},
                'type': node.node_type,
            }

        # Add connections
        for conn in connections:
            source_id = str(conn.source_node_id)
            target_id = str(conn.target_node_id)

            if source_id in graph and target_id in graph:
                graph[source_id]['outputs'].append({
                    'target': target_id,
                    'source_handle': conn.source_handle,
                    'target_handle': conn.target_handle,
                })
                graph[target_id]['inputs'].append({
                    'source': source_id,
                    'source_handle': conn.source_handle,
                    'target_handle': conn.target_handle,
                })

        return graph

    def _find_start_nodes(self, graph: Dict[str, Dict]) -> List[str]:
        """Find nodes with no incoming connections."""
        start_nodes = []
        for node_id, data in graph.items():
            if not data['inputs']:
                start_nodes.append(node_id)
        return start_nodes

    async def _execute_graph(
        self,
        graph: Dict[str, Dict],
        nodes: List,
        start_nodes: List[str],
        context: ExecutionContext
    ):
        """Execute the workflow graph."""
        # Track completed nodes
        completed: Set[str] = set()
        pending: Set[str] = set(start_nodes)

        while pending:
            # Check for pause/cancel
            if context.execution_id in self._paused:
                await self._wait_for_resume(context.execution_id)

            if context.execution_id in self._cancelled:
                break

            # Find nodes ready to execute (all inputs satisfied)
            ready = []
            for node_id in list(pending):
                node_data = graph[node_id]
                input_nodes = [inp['source'] for inp in node_data['inputs']]

                if all(inp in completed for inp in input_nodes):
                    ready.append(node_id)

            if not ready:
                # No nodes ready - might be a cycle or error
                break

            # Execute ready nodes in parallel
            tasks = []
            for node_id in ready:
                pending.discard(node_id)
                tasks.append(self._execute_single_node(
                    node_id,
                    graph,
                    context
                ))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for node_id, result in zip(ready, results):
                if isinstance(result, Exception):
                    # Handle error
                    error_result = NodeResult(
                        node_id=node_id,
                        status=NodeStatus.FAILED,
                        error=str(result),
                        completed_at=datetime.utcnow()
                    )
                    context.add_history(error_result)
                    await self._events.emit('node_error', context, node_id, result)
                else:
                    completed.add(node_id)
                    context.add_history(result)

                    # Add downstream nodes to pending
                    for output in graph[node_id]['outputs']:
                        target_id = output['target']
                        if target_id not in completed and target_id not in pending:
                            pending.add(target_id)

    async def _execute_single_node(
        self,
        node_id: str,
        graph: Dict[str, Dict],
        context: ExecutionContext
    ) -> NodeResult:
        """Execute a single node."""
        node_data = graph[node_id]
        node_type = node_data['type']
        node_config = node_data['config']

        # Get executor
        executor = self.get_executor(node_type)
        if not executor:
            return NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=f"No executor found for node type: {node_type}",
                completed_at=datetime.utcnow()
            )

        # Gather inputs from connected nodes
        inputs = {}
        for inp in node_data['inputs']:
            source_id = inp['source']
            source_handle = inp['source_handle']
            target_handle = inp['target_handle']

            source_output = context.get_node_output(source_id)
            if isinstance(source_output, dict) and source_handle:
                inputs[target_handle] = source_output.get(source_handle)
            else:
                inputs[target_handle] = source_output

        # Emit start event
        if context.on_node_start:
            context.on_node_start(node_id)
        await self._events.emit('node_start', context, node_id)

        # Execute node
        try:
            result = await executor.execute(node_config, inputs, context)
            context.set_node_output(node_id, result.output)

        except Exception as e:
            result = NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=str(e),
                completed_at=datetime.utcnow()
            )

        # Emit complete event
        if context.on_node_complete:
            context.on_node_complete(node_id, result)
        await self._events.emit('node_complete', context, node_id, result)

        return result

    async def execute_node(
        self,
        node_id: str,
        context: ExecutionContext
    ) -> NodeResult:
        """Execute a single node independently."""
        from apps.workflows.models import Node

        node = await asyncio.to_thread(Node.objects.get, id=node_id)

        executor = self.get_executor(node.node_type)
        if not executor:
            return NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=f"No executor for type: {node.node_type}"
            )

        return await executor.execute(
            node.config or {},
            {},
            context
        )

    async def pause(self, execution_id: str):
        """Pause a running execution."""
        if execution_id in self._executions:
            self._paused.add(execution_id)
            self._status[execution_id] = ExecutionStatus.PAUSED
            await self._events.emit(
                'execution_paused',
                self._executions[execution_id]
            )

    async def resume(self, execution_id: str):
        """Resume a paused execution."""
        if execution_id in self._paused:
            self._paused.discard(execution_id)
            self._status[execution_id] = ExecutionStatus.RUNNING
            await self._events.emit(
                'execution_resumed',
                self._executions[execution_id]
            )

    async def _wait_for_resume(self, execution_id: str):
        """Wait until execution is resumed or cancelled."""
        while execution_id in self._paused:
            if execution_id in self._cancelled:
                break
            await asyncio.sleep(0.5)

    async def cancel(self, execution_id: str):
        """Cancel an execution."""
        if execution_id in self._executions:
            self._cancelled.add(execution_id)
            self._paused.discard(execution_id)
            self._status[execution_id] = ExecutionStatus.CANCELLED
            await self._events.emit(
                'execution_cancelled',
                self._executions[execution_id]
            )

    def get_status(self, execution_id: str) -> ExecutionStatus:
        """Get execution status."""
        return self._status.get(execution_id, ExecutionStatus.PENDING)

    def on(self, event: str, callback):
        """Register event listener."""
        self._events.on(event, callback)

    def off(self, event: str, callback):
        """Remove event listener."""
        self._events.off(event, callback)


# Node executor implementations

class LLMNodeExecutor(BaseNodeExecutor):
    """Executor for LLM nodes."""

    @property
    def node_type(self) -> str:
        return 'llm'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        from apps.providers.llm.base import LLMMessage

        started_at = datetime.utcnow()

        # Get provider
        provider = context.get_provider('llm')
        if not provider:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error="LLM provider not configured",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        # Build messages
        system_prompt = node_config.get('system_prompt', '')
        system_prompt = context.substitute_variables(system_prompt)

        user_input = inputs.get('input', '') or node_config.get('user_prompt', '')
        user_input = context.substitute_variables(str(user_input))

        messages = []
        if system_prompt:
            messages.append(LLMMessage(role='system', content=system_prompt))
        if user_input:
            messages.append(LLMMessage(role='user', content=user_input))

        # Generate response
        try:
            response = await provider.generate_async(
                messages=messages,
                model=node_config.get('model', 'llama3.1:8b'),
                temperature=node_config.get('temperature', 0.7),
                max_tokens=node_config.get('max_tokens', 1024)
            )

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output={
                    'text': response.content,
                    'model': response.model,
                    'usage': response.usage.__dict__
                },
                started_at=started_at,
                completed_at=datetime.utcnow(),
                metrics={'tokens': response.usage.total_tokens}
            )

        except Exception as e:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )


class TTSNodeExecutor(BaseNodeExecutor):
    """Executor for TTS nodes."""

    @property
    def node_type(self) -> str:
        return 'tts'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        from apps.providers.tts.base import TTSRequest

        started_at = datetime.utcnow()

        provider = context.get_provider('tts')
        if not provider:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error="TTS provider not configured",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        text = inputs.get('input', '') or node_config.get('text', '')
        text = context.substitute_variables(str(text))

        request = TTSRequest(
            text=text,
            voice_id=node_config.get('voice_id', 'default'),
            language=node_config.get('language', 'en'),
            speed=node_config.get('speed', 1.0)
        )

        try:
            response = await provider.synthesize_async(request)

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output={
                    'audio_data': response.audio_data,
                    'duration_ms': response.duration_ms,
                    'format': response.format
                },
                started_at=started_at,
                completed_at=datetime.utcnow(),
                metrics={'duration_ms': response.duration_ms}
            )

        except Exception as e:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )


class WebSearchNodeExecutor(BaseNodeExecutor):
    """Executor for web search nodes."""

    @property
    def node_type(self) -> str:
        return 'web_search'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        provider = context.get_provider('browser')
        if not provider:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error="Browser provider not configured",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        query = inputs.get('input', '') or node_config.get('query', '')
        query = context.substitute_variables(str(query))

        try:
            results = await provider.search_async(
                query=query,
                max_results=node_config.get('max_results', 10)
            )

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output={
                    'query': query,
                    'results': [r.to_dict() for r in results]
                },
                started_at=started_at,
                completed_at=datetime.utcnow(),
                metrics={'result_count': len(results)}
            )

        except Exception as e:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )


class WebFetchNodeExecutor(BaseNodeExecutor):
    """Executor for web fetch nodes."""

    @property
    def node_type(self) -> str:
        return 'web_fetch'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        provider = context.get_provider('browser')
        if not provider:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error="Browser provider not configured",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        url = inputs.get('input', '') or node_config.get('url', '')
        url = context.substitute_variables(str(url))

        try:
            page = await provider.fetch_async(
                url=url,
                wait_time=node_config.get('wait_time', 3.0),
                extract_links=node_config.get('extract_links', True)
            )

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output=page.to_dict(),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )

        except Exception as e:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
