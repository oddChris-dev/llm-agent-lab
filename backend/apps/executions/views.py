"""
Views for execution management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from .models import Execution, ExecutionLog, ExecutionStatus
from .serializers import ExecutionSerializer, ExecutionDetailSerializer, ExecutionLogSerializer


class ExecutionFilter(filters.FilterSet):
    """
    Filter for execution list.
    """
    workflow_id = filters.UUIDFilter()
    status = filters.ChoiceFilter(choices=ExecutionStatus.choices)
    started_after = filters.DateTimeFilter(field_name='started_at', lookup_expr='gte')
    started_before = filters.DateTimeFilter(field_name='started_at', lookup_expr='lte')

    class Meta:
        model = Execution
        fields = ['workflow_id', 'status']


class ExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing executions.
    """
    permission_classes = [IsAuthenticated]
    filterset_class = ExecutionFilter
    ordering_fields = ['created_at', 'started_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Execution.objects.filter(workflow__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExecutionDetailSerializer
        return ExecutionSerializer

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Get logs for an execution.
        """
        execution = self.get_object()
        logs = execution.logs.all()

        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level)

        node_id = request.query_params.get('node_id')
        if node_id:
            logs = logs.filter(node_execution__node_id=node_id)

        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]

        serializer = ExecutionLogSerializer(logs, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Pause an execution.
        """
        execution = self.get_object()
        if execution.status != ExecutionStatus.RUNNING:
            return Response(
                {'error': 'Can only pause running executions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        execution.status = ExecutionStatus.PAUSED
        execution.save()
        return Response({'status': 'paused'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """
        Resume a paused execution.
        """
        execution = self.get_object()
        if execution.status != ExecutionStatus.PAUSED:
            return Response(
                {'error': 'Can only resume paused executions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        execution.status = ExecutionStatus.RUNNING
        execution.save()

        # Trigger async resume task
        from .tasks import resume_workflow
        resume_workflow.delay(str(execution.id))

        return Response({'status': 'running'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an execution.
        """
        execution = self.get_object()
        if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
            return Response(
                {'error': 'Cannot cancel this execution'},
                status=status.HTTP_400_BAD_REQUEST
            )
        execution.status = ExecutionStatus.CANCELLED
        execution.save()
        return Response({'status': 'cancelled'})
