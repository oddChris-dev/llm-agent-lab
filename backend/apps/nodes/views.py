"""
Views for node type discovery.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .registry import registry


class NodeTypeListView(APIView):
    """
    List all available node types.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category')

        if category:
            types = registry.list_by_category(category)
        else:
            types = registry.list_all()

        return Response({
            'data': [registry.to_dict(t) for t in types]
        })


class NodeTypeDetailView(APIView):
    """
    Get details of a specific node type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, type_id):
        node_type = registry.get(type_id)
        if not node_type:
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': f'Node type {type_id} not found'}},
                status=404
            )
        return Response({'data': registry.to_dict(node_type)})
