from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.core.exceptions import PermissionDenied
import os

from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.role:
            return Document.objects.none()

        queryset = Document.objects.all().select_related('resource', 'uploaded_by')

        # Limit documents to visible resources based on RBAC
        if user.role.name == 'manager':
            queryset = queryset.filter(resource__department=user.department)
        elif user.role.name == 'user':
            queryset = queryset.filter(resource__owner=user)

        # Support filtering by resource
        resource_id = self.request.query_params.get('resource')
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)

        return queryset

    def perform_create(self, serializer):
        # Validate resource ownership before permitting document creation
        resource = serializer.validated_data.get('resource')
        user = self.request.user

        if user.role.name == 'manager' and resource.department != user.department:
            raise PermissionDenied("You can only upload documents to resources in your department.")
        elif user.role.name == 'user' and resource.owner != user:
            raise PermissionDenied("You can only upload documents to resources you own.")

        serializer.save(uploaded_by=user)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        document = self.get_object()
        try:
            file_handle = document.file.open()
            response = FileResponse(file_handle, content_type=document.file_type)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(document.file.name)}"'
            return response
        except Exception as e:
            return Response({'error': f'Could not open file: {str(e)}'}, status=status.HTTP_404_NOT_FOUND)
