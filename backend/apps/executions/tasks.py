"""
Celery tasks for workflow execution.
"""

import logging
from typing import Optional, Dict, Any
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_workflow(self, execution_id: str, start_node_id: Optional[str] = None):
    """
    Execute a workflow asynchronously.

    Args:
        execution_id: ID of the Execution record
        start_node_id: Optional node to start from
    """
    from apps.executions.models import Execution, ExecutionStatus
    from apps.executions.engine import WorkflowExecutor, ExecutionContext
    from apps.providers.llm.ollama import OllamaProvider
    from apps.providers.tts.xtts import XTTSProvider
    from apps.providers.browser.selenium_browser import SeleniumBrowserProvider

    try:
        # Get execution record
        execution = Execution.objects.select_related('workflow', 'workflow__user').get(
            id=execution_id
        )

        # Update status
        execution.status = ExecutionStatus.RUNNING
        execution.save(update_fields=['status'])

        # Notify via WebSocket
        _notify_execution_update(execution_id, {
            'status': ExecutionStatus.RUNNING,
            'message': 'Execution started'
        })

        # Create execution context
        context = ExecutionContext(
            execution_id=str(execution.id),
            workflow_id=str(execution.workflow_id),
            user_id=str(execution.workflow.user_id) if execution.workflow.user else None,
            variables=execution.context.get('variables', {}),
            config=execution.context.get('config', {}),
        )

        # Initialize providers based on workflow config
        providers = _initialize_providers(execution.workflow.settings)
        context.providers = providers

        # Set up event callbacks
        context.on_node_start = lambda node_id: _on_node_start(execution_id, node_id)
        context.on_node_complete = lambda node_id, result: _on_node_complete(
            execution_id, node_id, result
        )

        # Create and run executor
        executor = WorkflowExecutor()
        _register_node_executors(executor)

        # Run the workflow
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            context = loop.run_until_complete(
                executor.execute(
                    workflow_id=str(execution.workflow_id),
                    context=context,
                    start_node_id=start_node_id
                )
            )
        finally:
            loop.close()

        # Update execution with results
        execution.status = ExecutionStatus.COMPLETED
        execution.context = {
            **execution.context,
            'variables': context.variables,
            'node_outputs': {k: _serialize_output(v) for k, v in context.node_outputs.items()},
        }
        execution.save()

        # Notify completion
        _notify_execution_update(execution_id, {
            'status': ExecutionStatus.COMPLETED,
            'message': 'Execution completed successfully'
        })

        return {'status': 'completed', 'execution_id': execution_id}

    except Exception as e:
        logger.exception(f"Workflow execution failed: {e}")

        # Update execution status
        try:
            execution = Execution.objects.get(id=execution_id)
            execution.status = ExecutionStatus.FAILED
            execution.context = {
                **execution.context,
                'error': str(e)
            }
            execution.save()
        except Exception:
            pass

        # Notify failure
        _notify_execution_update(execution_id, {
            'status': 'failed',
            'error': str(e)
        })

        # Retry if appropriate
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)

        return {'status': 'failed', 'error': str(e)}


@shared_task
def execute_node(execution_id: str, node_id: str):
    """
    Execute a single node within a workflow.

    Used for manual node execution or resuming paused workflows.
    """
    from apps.executions.models import Execution, NodeExecution, ExecutionStatus
    from apps.executions.engine import WorkflowExecutor, ExecutionContext

    try:
        execution = Execution.objects.get(id=execution_id)

        # Create minimal context
        context = ExecutionContext(
            execution_id=str(execution.id),
            workflow_id=str(execution.workflow_id),
            variables=execution.context.get('variables', {}),
        )

        # Initialize providers
        providers = _initialize_providers(execution.workflow.settings)
        context.providers = providers

        # Execute single node
        executor = WorkflowExecutor()
        _register_node_executors(executor)

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                executor.execute_node(node_id, context)
            )
        finally:
            loop.close()

        # Store node result
        NodeExecution.objects.update_or_create(
            execution=execution,
            node_id=node_id,
            defaults={
                'status': result.status.value,
                'output': _serialize_output(result.output),
                'error': result.error,
                'started_at': result.started_at,
                'completed_at': result.completed_at,
            }
        )

        return {
            'status': result.status.value,
            'output': _serialize_output(result.output)
        }

    except Exception as e:
        logger.exception(f"Node execution failed: {e}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def cleanup_stale_executions(timeout_hours: int = 24):
    """
    Clean up executions that have been running too long.
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.executions.models import Execution, ExecutionStatus

    cutoff = timezone.now() - timedelta(hours=timeout_hours)

    stale = Execution.objects.filter(
        status=ExecutionStatus.RUNNING,
        started_at__lt=cutoff
    )

    count = stale.count()
    stale.update(
        status=ExecutionStatus.FAILED,
        context={'error': 'Execution timed out'}
    )

    logger.info(f"Cleaned up {count} stale executions")
    return {'cleaned': count}


@shared_task
def cleanup_queue_items():
    """
    Clean up expired and stale queue items.
    """
    from apps.queues.models import Queue
    from apps.queues.services import QueueService

    total_expired = 0
    total_stale = 0

    for queue in Queue.objects.all():
        service = QueueService(queue)
        total_expired += service.cleanup_expired()
        total_stale += service.cleanup_stale()

    logger.info(f"Cleaned up {total_expired} expired, {total_stale} stale queue items")
    return {'expired': total_expired, 'stale': total_stale}


def _initialize_providers(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize providers based on workflow settings."""
    providers = {}

    # LLM Provider
    llm_config = settings.get('llm', {})
    llm_type = llm_config.get('type', 'ollama')

    if llm_type == 'ollama':
        from apps.providers.llm.ollama import OllamaProvider
        providers['llm'] = OllamaProvider(llm_config)
    elif llm_type == 'anthropic':
        from apps.providers.llm.anthropic import AnthropicProvider
        providers['llm'] = AnthropicProvider(llm_config)

    # TTS Provider (optional)
    tts_config = settings.get('tts', {})
    if tts_config.get('enabled', False):
        try:
            from apps.providers.tts.xtts import XTTSProvider
            providers['tts'] = XTTSProvider(tts_config)
        except ImportError:
            logger.warning("TTS provider not available")

    # Browser Provider (optional)
    browser_config = settings.get('browser', {})
    if browser_config.get('enabled', False):
        try:
            from apps.providers.browser.selenium_browser import SeleniumBrowserProvider
            providers['browser'] = SeleniumBrowserProvider(browser_config)
        except ImportError:
            logger.warning("Browser provider not available")

    return providers


def _register_node_executors(executor):
    """Register all node executors with the workflow executor."""
    from apps.executions.engine.executor import (
        LLMNodeExecutor,
        TTSNodeExecutor,
        WebSearchNodeExecutor,
        WebFetchNodeExecutor,
    )

    executor.register_executor(LLMNodeExecutor())
    executor.register_executor(TTSNodeExecutor())
    executor.register_executor(WebSearchNodeExecutor())
    executor.register_executor(WebFetchNodeExecutor())


def _on_node_start(execution_id: str, node_id: str):
    """Callback when a node starts executing."""
    from apps.executions.models import NodeExecution, Execution
    from django.utils import timezone

    execution = Execution.objects.get(id=execution_id)

    NodeExecution.objects.update_or_create(
        execution=execution,
        node_id=node_id,
        defaults={
            'status': 'running',
            'started_at': timezone.now(),
        }
    )

    _notify_node_update(execution_id, node_id, {
        'status': 'running',
        'node_id': node_id
    })


def _on_node_complete(execution_id: str, node_id: str, result):
    """Callback when a node completes."""
    from apps.executions.models import NodeExecution, Execution

    execution = Execution.objects.get(id=execution_id)

    NodeExecution.objects.update_or_create(
        execution=execution,
        node_id=node_id,
        defaults={
            'status': result.status.value,
            'output': _serialize_output(result.output),
            'error': result.error,
            'completed_at': result.completed_at,
        }
    )

    _notify_node_update(execution_id, node_id, {
        'status': result.status.value,
        'node_id': node_id,
        'output': _serialize_output(result.output),
        'error': result.error,
    })


def _notify_execution_update(execution_id: str, data: Dict):
    """Send execution update via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'execution_{execution_id}',
                {
                    'type': 'execution_update',
                    'data': data
                }
            )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket notification: {e}")


def _notify_node_update(execution_id: str, node_id: str, data: Dict):
    """Send node update via WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'execution_{execution_id}',
                {
                    'type': 'node_update',
                    'data': data
                }
            )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket notification: {e}")


def _serialize_output(output: Any) -> Any:
    """Serialize node output for storage."""
    if output is None:
        return None

    if isinstance(output, (str, int, float, bool)):
        return output

    if isinstance(output, dict):
        # Remove binary data from output
        return {
            k: v for k, v in output.items()
            if not isinstance(v, bytes)
        }

    if isinstance(output, (list, tuple)):
        return [_serialize_output(item) for item in output]

    return str(output)
