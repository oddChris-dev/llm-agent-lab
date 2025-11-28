"""
Unit tests for node executors.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from apps.executions.engine.node_executors import (
    ConditionalNodeExecutor,
    DelayNodeExecutor,
    LoopNodeExecutor,
    VariableNodeExecutor,
    TransformNodeExecutor,
    MergeNodeExecutor,
    HTTPRequestNodeExecutor,
    TextProcessNodeExecutor,
    OutputNodeExecutor,
    LogNodeExecutor,
)


class TestConditionalNodeExecutor:
    """Tests for ConditionalNodeExecutor."""

    def test_equals_condition_true(self):
        """Test equals condition evaluates to true."""
        executor = ConditionalNodeExecutor()
        config = {
            'conditions': [
                {'field': 'status', 'operator': 'equals', 'value': 'active'}
            ]
        }
        inputs = {'status': 'active'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] is True
        assert result['branch'] == 'true'

    def test_equals_condition_false(self):
        """Test equals condition evaluates to false."""
        executor = ConditionalNodeExecutor()
        config = {
            'conditions': [
                {'field': 'status', 'operator': 'equals', 'value': 'active'}
            ]
        }
        inputs = {'status': 'inactive'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] is False
        assert result['branch'] == 'false'

    def test_contains_operator(self):
        """Test contains operator."""
        executor = ConditionalNodeExecutor()
        config = {
            'conditions': [
                {'field': 'message', 'operator': 'contains', 'value': 'hello'}
            ]
        }
        inputs = {'message': 'Say hello world'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] is True

    def test_greater_than_operator(self):
        """Test greater_than operator."""
        executor = ConditionalNodeExecutor()
        config = {
            'conditions': [
                {'field': 'score', 'operator': 'greater_than', 'value': 50}
            ]
        }
        inputs = {'score': 75}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] is True

    def test_multiple_conditions_and(self):
        """Test multiple conditions with AND logic."""
        executor = ConditionalNodeExecutor()
        config = {
            'conditions': [
                {'field': 'active', 'operator': 'equals', 'value': True},
                {'field': 'score', 'operator': 'greater_than', 'value': 50}
            ],
            'match_all': True
        }
        inputs = {'active': True, 'score': 60}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] is True

    def test_multiple_conditions_or(self):
        """Test multiple conditions with OR logic."""
        executor = ConditionalNodeExecutor()
        config = {
            'conditions': [
                {'field': 'role', 'operator': 'equals', 'value': 'admin'},
                {'field': 'role', 'operator': 'equals', 'value': 'superuser'}
            ],
            'match_all': False
        }
        inputs = {'role': 'superuser'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] is True


class TestDelayNodeExecutor:
    """Tests for DelayNodeExecutor."""

    @patch('asyncio.sleep')
    def test_delay_seconds(self, mock_sleep):
        """Test delay with seconds."""
        mock_sleep.return_value = None
        executor = DelayNodeExecutor()
        config = {'delay_seconds': 5}
        inputs = {'data': 'test'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        mock_sleep.assert_called_once_with(5)
        assert result['data'] == 'test'

    @patch('asyncio.sleep')
    def test_delay_dynamic_from_input(self, mock_sleep):
        """Test delay from input value."""
        mock_sleep.return_value = None
        executor = DelayNodeExecutor()
        config = {'delay_field': 'wait_time'}
        inputs = {'wait_time': 10}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        mock_sleep.assert_called_once_with(10)


class TestVariableNodeExecutor:
    """Tests for VariableNodeExecutor."""

    def test_set_variable(self):
        """Test setting a variable."""
        executor = VariableNodeExecutor()
        config = {
            'operation': 'set',
            'name': 'counter',
            'value': 42
        }
        inputs = {}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['counter'] == 42

    def test_get_variable(self):
        """Test getting a variable from inputs."""
        executor = VariableNodeExecutor()
        config = {
            'operation': 'get',
            'name': 'user_id'
        }
        inputs = {'user_id': 'abc123'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['value'] == 'abc123'

    def test_increment_variable(self):
        """Test incrementing a numeric variable."""
        executor = VariableNodeExecutor()
        config = {
            'operation': 'increment',
            'name': 'count',
            'amount': 5
        }
        inputs = {'count': 10}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['count'] == 15


class TestTransformNodeExecutor:
    """Tests for TransformNodeExecutor."""

    def test_map_transform(self):
        """Test map transformation."""
        executor = TransformNodeExecutor()
        config = {
            'transform': 'map',
            'field': 'items',
            'expression': 'x * 2'
        }
        inputs = {'items': [1, 2, 3, 4, 5]}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['items'] == [2, 4, 6, 8, 10]

    def test_filter_transform(self):
        """Test filter transformation."""
        executor = TransformNodeExecutor()
        config = {
            'transform': 'filter',
            'field': 'numbers',
            'expression': 'x > 5'
        }
        inputs = {'numbers': [1, 3, 7, 9, 2, 8]}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['numbers'] == [7, 9, 8]

    def test_reduce_transform(self):
        """Test reduce transformation."""
        executor = TransformNodeExecutor()
        config = {
            'transform': 'reduce',
            'field': 'values',
            'expression': 'acc + x',
            'initial': 0
        }
        inputs = {'values': [1, 2, 3, 4, 5]}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['result'] == 15


class TestMergeNodeExecutor:
    """Tests for MergeNodeExecutor."""

    def test_merge_inputs(self):
        """Test merging multiple inputs."""
        executor = MergeNodeExecutor()
        config = {'strategy': 'combine'}
        inputs = {
            'input1': {'name': 'John'},
            'input2': {'age': 30},
            'input3': {'city': 'NYC'}
        }

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['name'] == 'John'
        assert result['age'] == 30
        assert result['city'] == 'NYC'

    def test_merge_with_override(self):
        """Test merge with key override."""
        executor = MergeNodeExecutor()
        config = {'strategy': 'override'}
        inputs = {
            'base': {'a': 1, 'b': 2},
            'override': {'b': 3, 'c': 4}
        }

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['a'] == 1
        assert result['b'] == 3
        assert result['c'] == 4


class TestTextProcessNodeExecutor:
    """Tests for TextProcessNodeExecutor."""

    def test_uppercase(self):
        """Test uppercase operation."""
        executor = TextProcessNodeExecutor()
        config = {'operation': 'uppercase', 'field': 'text'}
        inputs = {'text': 'Hello World'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['text'] == 'HELLO WORLD'

    def test_lowercase(self):
        """Test lowercase operation."""
        executor = TextProcessNodeExecutor()
        config = {'operation': 'lowercase', 'field': 'text'}
        inputs = {'text': 'Hello World'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['text'] == 'hello world'

    def test_split(self):
        """Test split operation."""
        executor = TextProcessNodeExecutor()
        config = {
            'operation': 'split',
            'field': 'text',
            'separator': ','
        }
        inputs = {'text': 'a,b,c,d'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['text'] == ['a', 'b', 'c', 'd']

    def test_join(self):
        """Test join operation."""
        executor = TextProcessNodeExecutor()
        config = {
            'operation': 'join',
            'field': 'items',
            'separator': ' - '
        }
        inputs = {'items': ['apple', 'banana', 'cherry']}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['items'] == 'apple - banana - cherry'

    def test_replace(self):
        """Test replace operation."""
        executor = TextProcessNodeExecutor()
        config = {
            'operation': 'replace',
            'field': 'text',
            'pattern': 'foo',
            'replacement': 'bar'
        }
        inputs = {'text': 'foo and foo again'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['text'] == 'bar and bar again'

    def test_template(self):
        """Test template operation."""
        executor = TextProcessNodeExecutor()
        config = {
            'operation': 'template',
            'template': 'Hello, {name}! You have {count} messages.'
        }
        inputs = {'name': 'Alice', 'count': 5}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['text'] == 'Hello, Alice! You have 5 messages.'


class TestOutputNodeExecutor:
    """Tests for OutputNodeExecutor."""

    def test_output_returns_inputs(self):
        """Test output node returns all inputs."""
        executor = OutputNodeExecutor()
        config = {}
        inputs = {'result': 'success', 'data': [1, 2, 3]}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result == inputs

    def test_output_with_selected_fields(self):
        """Test output with selected fields only."""
        executor = OutputNodeExecutor()
        config = {'fields': ['name', 'email']}
        inputs = {
            'name': 'John',
            'email': 'john@example.com',
            'password': 'secret'
        }

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result == {'name': 'John', 'email': 'john@example.com'}
        assert 'password' not in result


class TestLogNodeExecutor:
    """Tests for LogNodeExecutor."""

    @patch('logging.getLogger')
    def test_log_info(self, mock_get_logger):
        """Test logging at info level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        executor = LogNodeExecutor()
        config = {
            'level': 'info',
            'message': 'Processing completed'
        }
        inputs = {'status': 'done'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        mock_logger.info.assert_called_once()
        assert result['status'] == 'done'

    @patch('logging.getLogger')
    def test_log_with_template(self, mock_get_logger):
        """Test logging with template message."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        executor = LogNodeExecutor()
        config = {
            'level': 'warning',
            'message': 'User {user_id} performed action {action}'
        }
        inputs = {'user_id': '123', 'action': 'delete'}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        call_args = mock_logger.warning.call_args[0][0]
        assert '123' in call_args
        assert 'delete' in call_args


class TestHTTPRequestNodeExecutor:
    """Tests for HTTPRequestNodeExecutor."""

    @patch('httpx.AsyncClient')
    def test_get_request(self, mock_client_class):
        """Test HTTP GET request."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_response.headers = {'content-type': 'application/json'}
        mock_client.request = AsyncMock(return_value=mock_response)

        executor = HTTPRequestNodeExecutor()
        config = {
            'method': 'GET',
            'url': 'https://api.example.com/data'
        }
        inputs = {}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['status_code'] == 200
        assert result['body'] == {'data': 'test'}
        mock_client.request.assert_called_once()

    @patch('httpx.AsyncClient')
    def test_post_request_with_body(self, mock_client_class):
        """Test HTTP POST request with JSON body."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1, 'created': True}
        mock_response.headers = {'content-type': 'application/json'}
        mock_client.request = AsyncMock(return_value=mock_response)

        executor = HTTPRequestNodeExecutor()
        config = {
            'method': 'POST',
            'url': 'https://api.example.com/items',
            'headers': {'Authorization': 'Bearer token123'}
        }
        inputs = {'name': 'New Item', 'value': 42}

        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(config, inputs)
        )

        assert result['status_code'] == 201
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs['json'] == inputs
