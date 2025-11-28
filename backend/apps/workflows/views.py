"""
Views for workflow management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters import rest_framework as filters
from django.db.models import Count
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Workflow, Node, Connection, WorkflowStatus
from .serializers import (
    WorkflowListSerializer,
    WorkflowDetailSerializer,
    WorkflowCreateSerializer,
    WorkflowUpdateSerializer,
    WorkflowDuplicateSerializer,
    NodeSerializer,
    NodeCreateSerializer,
    NodeUpdateSerializer,
    NodeBatchUpdateSerializer,
    ConnectionSerializer,
    ConnectionCreateSerializer,
)


class WorkflowFilter(filters.FilterSet):
    """
    Filter for workflow list endpoint.
    """
    status = filters.ChoiceFilter(choices=WorkflowStatus.choices)
    is_template = filters.BooleanFilter()
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Workflow
        fields = ['status', 'is_template']

    def filter_search(self, queryset, name, value):
        return queryset.filter(name__icontains=value)


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for workflow CRUD operations.

    list:
        Return list of workflows for the authenticated user.

    retrieve:
        Return full workflow details including nodes and connections.

    create:
        Create a new workflow.

    update/partial_update:
        Update an existing workflow.

    destroy:
        Soft-delete a workflow.
    """
    permission_classes = [IsAuthenticated]
    filterset_class = WorkflowFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-updated_at']

    def get_queryset(self):
        return Workflow.objects.filter(user=self.request.user).annotate(
            node_count=Count('nodes'),
            connection_count=Count('connections')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return WorkflowListSerializer
        elif self.action == 'retrieve':
            return WorkflowDetailSerializer
        elif self.action == 'create':
            return WorkflowCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WorkflowUpdateSerializer
        elif self.action == 'duplicate':
            return WorkflowDuplicateSerializer
        return WorkflowDetailSerializer

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def duplicate(self, request, pk=None):
        """
        Create a copy of this workflow with all nodes and connections.
        Uses database transaction to ensure atomicity.
        """
        workflow = self.get_object()
        serializer = WorkflowDuplicateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_workflow = workflow.duplicate(
            new_name=serializer.validated_data.get('name'),
            user=request.user
        )

        return Response(
            WorkflowDetailSerializer(new_workflow).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Start execution of this workflow.
        """
        workflow = self.get_object()

        if workflow.status != WorkflowStatus.ACTIVE:
            return Response(
                {'error': 'Workflow must be active to execute'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Import here to avoid circular imports
        from apps.executions.models import Execution
        from apps.executions.serializers import ExecutionSerializer

        execution = Execution.objects.create(
            workflow=workflow,
            trigger_type='api',
            trigger_data=request.data.get('trigger_data', {}),
        )

        # Start async execution task
        from apps.executions.tasks import execute_workflow
        execute_workflow.delay(str(execution.id))

        return Response(
            ExecutionSerializer(execution).data,
            status=status.HTTP_202_ACCEPTED
        )


class NodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for node operations within a workflow.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workflow_id = self.kwargs['workflow_pk']
        return Node.objects.filter(
            workflow_id=workflow_id,
            workflow__user=self.request.user
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return NodeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NodeUpdateSerializer
        return NodeSerializer

    def perform_create(self, serializer):
        workflow_id = self.kwargs['workflow_pk']
        workflow = Workflow.objects.get(id=workflow_id, user=self.request.user)
        serializer.save(workflow=workflow)

    @action(detail=False, methods=['patch'])
    def batch(self, request, workflow_pk=None):
        """
        Batch update multiple nodes (e.g., for canvas drag operations).
        """
        serializer = NodeBatchUpdateSerializer(data=request.data.get('updates', []), many=True)
        serializer.is_valid(raise_exception=True)

        nodes = {str(n.id): n for n in self.get_queryset()}

        for update in serializer.validated_data:
            node_id = str(update['id'])
            if node_id in nodes:
                node = nodes[node_id]
                if 'position' in update:
                    node.position_x = update['position'].get('x', node.position_x)
                    node.position_y = update['position'].get('y', node.position_y)
                if 'config' in update:
                    node.config.update(update['config'])
                node.save()

        return Response({'updated': len(serializer.validated_data)})


class ConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for connection operations within a workflow.
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        workflow_id = self.kwargs['workflow_pk']
        return Connection.objects.filter(
            workflow_id=workflow_id,
            workflow__user=self.request.user
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return ConnectionCreateSerializer
        return ConnectionSerializer

    def perform_create(self, serializer):
        workflow_id = self.kwargs['workflow_pk']
        workflow = Workflow.objects.get(id=workflow_id, user=self.request.user)
        serializer.save(workflow=workflow)


class DashboardStatsView(APIView):
    """
    API view for dashboard statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.executions.models import Execution, ExecutionStatus

        user = request.user
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Count workflows
        total_workflows = Workflow.objects.filter(user=user).count()
        active_workflows = Workflow.objects.filter(
            user=user, status=WorkflowStatus.ACTIVE
        ).count()

        # Count executions
        running_executions = Execution.objects.filter(
            workflow__user=user,
            status=ExecutionStatus.RUNNING
        ).count()

        pending_executions = Execution.objects.filter(
            workflow__user=user,
            status=ExecutionStatus.PENDING
        ).count()

        completed_today = Execution.objects.filter(
            workflow__user=user,
            status=ExecutionStatus.COMPLETED,
            finished_at__gte=today
        ).count()

        failed_today = Execution.objects.filter(
            workflow__user=user,
            status=ExecutionStatus.FAILED,
            finished_at__gte=today
        ).count()

        return Response({
            'total_workflows': total_workflows,
            'active_workflows': active_workflows,
            'running_executions': running_executions,
            'pending_executions': pending_executions,
            'queued_tasks': pending_executions + running_executions,
            'completed_today': completed_today,
            'failed_today': failed_today,
        })
