"""
Additional node executors for workflow processing.

Provides executors for:
- Control flow (conditional, loop, delay)
- Data manipulation (variable, transform, merge)
- Queue operations (push, pop)
- External integrations (HTTP, image generation)
"""

import re
import json
import asyncio
import httpx
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseNodeExecutor, NodeResult, NodeStatus, ExecutionContext


# ============================================================================
# Control Flow Nodes
# ============================================================================

class ConditionalNodeExecutor(BaseNodeExecutor):
    """
    Conditional branching based on input conditions.

    Config:
        conditions: List of {expression, output_port} pairs
        default_port: Port to use if no conditions match
    """

    @property
    def node_type(self) -> str:
        return 'conditional'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        conditions = node_config.get('conditions', [])
        default_port = node_config.get('default_port', 'else')
        input_value = inputs.get('input')

        matched_port = default_port

        for condition in conditions:
            expression = condition.get('expression', '')
            output_port = condition.get('output_port', 'then')

            if self._evaluate_condition(expression, input_value, context):
                matched_port = output_port
                break

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output={
                'matched_port': matched_port,
                'value': input_value,
                matched_port: input_value  # Route to matched port
            },
            started_at=started_at,
            completed_at=datetime.utcnow()
        )

    def _evaluate_condition(
        self,
        expression: str,
        input_value: Any,
        context: ExecutionContext
    ) -> bool:
        """Evaluate a condition expression."""
        if not expression:
            return False

        # Simple expression evaluation
        # Supports: ==, !=, >, <, >=, <=, contains, startswith, endswith
        expression = context.substitute_variables(expression)

        # Parse expression
        patterns = [
            (r'(.+?)\s*==\s*(.+)', lambda a, b: str(a).strip() == str(b).strip()),
            (r'(.+?)\s*!=\s*(.+)', lambda a, b: str(a).strip() != str(b).strip()),
            (r'(.+?)\s*>=\s*(.+)', lambda a, b: float(a) >= float(b)),
            (r'(.+?)\s*<=\s*(.+)', lambda a, b: float(a) <= float(b)),
            (r'(.+?)\s*>\s*(.+)', lambda a, b: float(a) > float(b)),
            (r'(.+?)\s*<\s*(.+)', lambda a, b: float(a) < float(b)),
            (r'(.+?)\s+contains\s+(.+)', lambda a, b: b.strip() in str(a)),
            (r'(.+?)\s+startswith\s+(.+)', lambda a, b: str(a).startswith(b.strip())),
            (r'(.+?)\s+endswith\s+(.+)', lambda a, b: str(a).endswith(b.strip())),
        ]

        for pattern, evaluator in patterns:
            match = re.match(pattern, expression, re.IGNORECASE)
            if match:
                try:
                    left = match.group(1).strip()
                    right = match.group(2).strip()

                    # Replace 'input' with actual value
                    if left.lower() == 'input':
                        left = str(input_value) if input_value else ''
                    if right.lower() == 'input':
                        right = str(input_value) if input_value else ''

                    return evaluator(left, right)
                except (ValueError, TypeError):
                    return False

        # If it's just a truthy check
        if expression.lower() == 'input':
            return bool(input_value)

        return bool(expression)


class DelayNodeExecutor(BaseNodeExecutor):
    """
    Delay execution for a specified time.

    Config:
        delay_seconds: Number of seconds to delay
        delay_ms: Number of milliseconds to delay
    """

    @property
    def node_type(self) -> str:
        return 'delay'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        delay_seconds = node_config.get('delay_seconds', 0)
        delay_ms = node_config.get('delay_ms', 0)

        total_delay = delay_seconds + (delay_ms / 1000)

        if total_delay > 0:
            await asyncio.sleep(total_delay)

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output=inputs.get('input'),
            started_at=started_at,
            completed_at=datetime.utcnow(),
            metrics={'delay_seconds': total_delay}
        )


class LoopNodeExecutor(BaseNodeExecutor):
    """
    Loop over items in an array.

    Config:
        max_iterations: Maximum number of iterations (safety limit)
    """

    @property
    def node_type(self) -> str:
        return 'loop'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        items = inputs.get('items', inputs.get('input', []))
        max_iterations = node_config.get('max_iterations', 1000)

        if not isinstance(items, (list, tuple)):
            items = [items] if items else []

        # Limit iterations
        items = items[:max_iterations]

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output={
                'items': items,
                'count': len(items),
                'current_index': 0,
            },
            started_at=started_at,
            completed_at=datetime.utcnow(),
            metrics={'iteration_count': len(items)}
        )


# ============================================================================
# Data Manipulation Nodes
# ============================================================================

class VariableNodeExecutor(BaseNodeExecutor):
    """
    Get or set workflow variables.

    Config:
        operation: 'get' or 'set'
        variable_name: Name of the variable
        default_value: Default value if variable doesn't exist
    """

    @property
    def node_type(self) -> str:
        return 'variable'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        operation = node_config.get('operation', 'get')
        variable_name = node_config.get('variable_name', '')
        default_value = node_config.get('default_value')

        if operation == 'set':
            value = inputs.get('input', inputs.get('value'))
            context.set_variable(variable_name, value)
            output = {'variable': variable_name, 'value': value}
        else:
            value = context.get_variable(variable_name, default_value)
            output = value

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output=output,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )


class TransformNodeExecutor(BaseNodeExecutor):
    """
    Transform data using JSONPath or simple operations.

    Config:
        operation: 'extract', 'template', 'json_parse', 'json_stringify'
        path: JSONPath or key path for extraction
        template: Template string with {key} placeholders
    """

    @property
    def node_type(self) -> str:
        return 'transform'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        operation = node_config.get('operation', 'extract')
        input_data = inputs.get('input')

        try:
            if operation == 'extract':
                path = node_config.get('path', '')
                output = self._extract_path(input_data, path)

            elif operation == 'template':
                template = node_config.get('template', '')
                template = context.substitute_variables(template)
                if isinstance(input_data, dict):
                    output = template.format(**input_data)
                else:
                    output = template.format(input=input_data)

            elif operation == 'json_parse':
                output = json.loads(input_data) if isinstance(input_data, str) else input_data

            elif operation == 'json_stringify':
                output = json.dumps(input_data, indent=2)

            else:
                output = input_data

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output=output,
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

    def _extract_path(self, data: Any, path: str) -> Any:
        """Extract value at path from data."""
        if not path:
            return data

        parts = path.split('.')
        result = data

        for part in parts:
            if isinstance(result, dict):
                result = result.get(part)
            elif isinstance(result, (list, tuple)):
                try:
                    result = result[int(part)]
                except (ValueError, IndexError):
                    result = None
            else:
                result = None

            if result is None:
                break

        return result


class MergeNodeExecutor(BaseNodeExecutor):
    """
    Merge multiple inputs into a single output.

    Config:
        mode: 'object' (merge dicts), 'array' (combine into list), 'concat' (string concat)
    """

    @property
    def node_type(self) -> str:
        return 'merge'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        mode = node_config.get('mode', 'object')

        if mode == 'object':
            output = {}
            for key, value in inputs.items():
                if isinstance(value, dict):
                    output.update(value)
                else:
                    output[key] = value

        elif mode == 'array':
            output = list(inputs.values())

        elif mode == 'concat':
            output = ''.join(str(v) for v in inputs.values() if v)

        else:
            output = inputs

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output=output,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )


# ============================================================================
# Queue Nodes
# ============================================================================

class QueuePushNodeExecutor(BaseNodeExecutor):
    """
    Push item to a queue.

    Config:
        queue_slug: Slug of the queue to push to
        priority: Item priority (default 0)
    """

    @property
    def node_type(self) -> str:
        return 'queue_push'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        from apps.queues.services import QueueService

        started_at = datetime.utcnow()

        queue_slug = node_config.get('queue_slug', '')
        queue_slug = context.substitute_variables(queue_slug)
        priority = node_config.get('priority', 0)
        data = inputs.get('input')

        try:
            service = QueueService.get_by_slug(queue_slug)
            item = service.push(
                data=data,
                priority=priority,
                source_execution_id=context.execution_id,
            )

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output={
                    'item_id': str(item.id),
                    'queue': queue_slug,
                    'status': item.status
                },
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


class QueuePopNodeExecutor(BaseNodeExecutor):
    """
    Pop item from a queue.

    Config:
        queue_slug: Slug of the queue to pop from
        consumer_id: Optional consumer identifier
        wait_if_empty: Wait for item if queue is empty
        wait_timeout: Timeout for waiting (seconds)
    """

    @property
    def node_type(self) -> str:
        return 'queue_pop'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        from apps.queues.services import QueueService

        started_at = datetime.utcnow()

        queue_slug = node_config.get('queue_slug', '')
        queue_slug = context.substitute_variables(queue_slug)
        consumer_id = node_config.get('consumer_id')
        wait_if_empty = node_config.get('wait_if_empty', False)
        wait_timeout = node_config.get('wait_timeout', 30)

        try:
            service = QueueService.get_by_slug(queue_slug)

            item = service.pop(consumer_id)

            # Wait for item if configured
            if not item and wait_if_empty:
                elapsed = 0
                while not item and elapsed < wait_timeout:
                    await asyncio.sleep(1)
                    elapsed += 1
                    item = service.pop(consumer_id)

            if item:
                return NodeResult(
                    node_id='',
                    status=NodeStatus.COMPLETED,
                    output={
                        'item_id': str(item.id),
                        'data': item.data,
                        'queue': queue_slug
                    },
                    started_at=started_at,
                    completed_at=datetime.utcnow()
                )
            else:
                return NodeResult(
                    node_id='',
                    status=NodeStatus.COMPLETED,
                    output={'data': None, 'empty': True},
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


# ============================================================================
# External Integration Nodes
# ============================================================================

class HTTPRequestNodeExecutor(BaseNodeExecutor):
    """
    Make HTTP requests.

    Config:
        url: Request URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: Request headers
        body: Request body
        timeout: Request timeout in seconds
    """

    @property
    def node_type(self) -> str:
        return 'http_request'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        url = node_config.get('url', '')
        url = context.substitute_variables(url)
        method = node_config.get('method', 'GET').upper()
        headers = node_config.get('headers', {})
        body = inputs.get('input') or node_config.get('body')
        timeout = node_config.get('timeout', 30)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    content=body if isinstance(body, str) else None,
                )

                # Try to parse JSON response
                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text

                return NodeResult(
                    node_id='',
                    status=NodeStatus.COMPLETED,
                    output={
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'data': response_data,
                        'url': str(response.url)
                    },
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    metrics={'status_code': response.status_code}
                )

        except Exception as e:
            return NodeResult(
                node_id='',
                status=NodeStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow()
            )


class TextProcessNodeExecutor(BaseNodeExecutor):
    """
    Text processing operations.

    Config:
        operation: 'split', 'join', 'replace', 'regex', 'trim', 'upper', 'lower'
        pattern: Pattern for split/replace/regex
        replacement: Replacement string
        separator: Separator for join
    """

    @property
    def node_type(self) -> str:
        return 'text_process'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        operation = node_config.get('operation', 'trim')
        input_text = str(inputs.get('input', ''))

        try:
            if operation == 'split':
                pattern = node_config.get('pattern', '\n')
                output = input_text.split(pattern)

            elif operation == 'join':
                separator = node_config.get('separator', '\n')
                items = inputs.get('input', [])
                if isinstance(items, (list, tuple)):
                    output = separator.join(str(item) for item in items)
                else:
                    output = str(items)

            elif operation == 'replace':
                pattern = node_config.get('pattern', '')
                replacement = node_config.get('replacement', '')
                output = input_text.replace(pattern, replacement)

            elif operation == 'regex':
                pattern = node_config.get('pattern', '')
                replacement = node_config.get('replacement', '')
                output = re.sub(pattern, replacement, input_text)

            elif operation == 'trim':
                output = input_text.strip()

            elif operation == 'upper':
                output = input_text.upper()

            elif operation == 'lower':
                output = input_text.lower()

            else:
                output = input_text

            return NodeResult(
                node_id='',
                status=NodeStatus.COMPLETED,
                output=output,
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


# ============================================================================
# Output Nodes
# ============================================================================

class OutputNodeExecutor(BaseNodeExecutor):
    """
    Workflow output node - marks data as workflow output.

    Config:
        output_name: Name for this output
    """

    @property
    def node_type(self) -> str:
        return 'output'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        started_at = datetime.utcnow()

        output_name = node_config.get('output_name', 'output')
        input_data = inputs.get('input')

        # Store in context as workflow output
        outputs = context.get_variable('_workflow_outputs', {})
        outputs[output_name] = input_data
        context.set_variable('_workflow_outputs', outputs)

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output=input_data,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )


class LogNodeExecutor(BaseNodeExecutor):
    """
    Log data for debugging.

    Config:
        log_level: 'debug', 'info', 'warning', 'error'
        message: Optional message prefix
    """

    @property
    def node_type(self) -> str:
        return 'log'

    async def execute(
        self,
        node_config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> NodeResult:
        import logging
        started_at = datetime.utcnow()

        log_level = node_config.get('log_level', 'info')
        message = node_config.get('message', '')
        input_data = inputs.get('input')

        logger = logging.getLogger('apps.executions')

        log_message = f"{message}: {input_data}" if message else str(input_data)

        if log_level == 'debug':
            logger.debug(log_message)
        elif log_level == 'warning':
            logger.warning(log_message)
        elif log_level == 'error':
            logger.error(log_message)
        else:
            logger.info(log_message)

        return NodeResult(
            node_id='',
            status=NodeStatus.COMPLETED,
            output=input_data,
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
