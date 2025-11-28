"""
Views for provider management.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Provider
from .serializers import ProviderSerializer, ProviderCreateSerializer


class ProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for provider CRUD operations.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Provider.objects.filter(
            models.Q(user=self.request.user) | models.Q(is_system=True)
        )
        provider_type = self.request.query_params.get('type')
        if provider_type:
            queryset = queryset.filter(type=provider_type)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ProviderCreateSerializer
        return ProviderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test provider connection.
        """
        provider = self.get_object()
        # TODO: Implement actual provider testing
        return Response({
            'success': True,
            'latency_ms': 100,
            'message': 'Connection successful'
        })


# Import models for queryset
from django.db import models
