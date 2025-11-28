"""
Serializers for execution models.
"""

from rest_framework import serializers
from .models import Execution, NodeExecution, ExecutionLog


class NodeExecutionSerializer(serializers.ModelSerializer):
    """
    Serializer for NodeExecution model.
    """
    node_name = serializers.CharField(source='node.name', read_only=True)
    node_type = serializers.CharField(source='node.type', read_only=True)

    class Meta:
        model = NodeExecution
        fields = [
            'id', 'node_id', 'node_name', 'node_type',
            'status', 'input_data', 'output_data',
            'error_message', 'retry_count',
            'queued_at', 'started_at', 'finished_at', 'duration_ms'
        ]


class ExecutionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ExecutionLog model.
    """
    node_id = serializers.UUIDField(source='node_execution.node_id', read_only=True)
    node_name = serializers.CharField(source='node_execution.node.name', read_only=True)

    class Meta:
        model = ExecutionLog
        fields = ['id', 'level', 'message', 'data', 'node_id', 'node_name', 'timestamp']


class ExecutionSerializer(serializers.ModelSerializer):
    """
    Serializer for Execution model.
    """
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Execution
        fields = [
            'id', 'workflow_id', 'workflow_name', 'status',
            'progress', 'trigger_type', 'trigger_data',
            'error_message', 'error_node_id',
            'started_at', 'finished_at', 'created_at'
        ]

    def get_progress(self, obj):
        total = obj.total_nodes or 1
        return {
            'total_nodes': obj.total_nodes,
            'completed_nodes': obj.completed_nodes,
            'failed_nodes': obj.failed_nodes,
            'percentage': round((obj.completed_nodes / total) * 100) if total > 0 else 0
        }


class ExecutionDetailSerializer(ExecutionSerializer):
    """
    Detailed execution serializer with node executions.
    """
    node_executions = NodeExecutionSerializer(many=True, read_only=True)

    class Meta(ExecutionSerializer.Meta):
        fields = ExecutionSerializer.Meta.fields + ['node_executions', 'context']
