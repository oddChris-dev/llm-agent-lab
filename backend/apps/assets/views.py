"""
Views for asset management.
"""

import os
import hashlib
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Asset


class AssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for asset CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = Asset.objects.filter(user=self.request.user)
        asset_type = self.request.query_params.get('type')
        if asset_type:
            queryset = queryset.filter(type=asset_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Upload a new asset.
        """
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate file path
        filename = file.name
        asset_type = request.data.get('type', 'other')
        file_path = os.path.join(
            settings.AGENT_LAB['ASSET_STORAGE_PATH'],
            asset_type,
            filename
        )

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Calculate checksum while saving
        hasher = hashlib.sha256()
        with open(file_path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
                hasher.update(chunk)

        # Create asset record
        asset = Asset.objects.create(
            name=request.data.get('name', filename),
            type=asset_type,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            checksum=hasher.hexdigest(),
            metadata=request.data.get('metadata', {}),
            user=request.user,
        )

        return Response({
            'id': str(asset.id),
            'name': asset.name,
            'type': asset.type,
            'file_size': asset.file_size,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download asset file.
        """
        asset = self.get_object()
        if not os.path.exists(asset.file_path):
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update usage tracking
        from django.utils import timezone
        asset.usage_count += 1
        asset.last_used_at = timezone.now()
        asset.save(update_fields=['usage_count', 'last_used_at'])

        return FileResponse(
            open(asset.file_path, 'rb'),
            content_type=asset.mime_type or 'application/octet-stream',
            filename=asset.name
        )
