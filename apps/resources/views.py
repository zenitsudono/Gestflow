from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.db.models import Count

from .models import Resource, Category
from .serializers import ResourceSerializer, CategorySerializer
from apps.accounts.permissions import ResourcePermission, IsAdminOrManager

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrManager()]
        return [permissions.IsAuthenticated()]

class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated, ResourcePermission]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.role:
            return Resource.objects.none()
            
        queryset = Resource.objects.all().select_related('category', 'owner')
        
        # Queryset filtering based on Role-Based Access Control
        if user.role.name == 'manager':
            queryset = queryset.filter(department=user.department)
        elif user.role.name == 'user':
            queryset = queryset.filter(owner=user)
            
        # Optional filter for archived resources (exclude by default, except for detail actions)
        if not self.detail:
            is_archived = self.request.query_params.get('is_archived', 'false')
            if is_archived.lower() == 'true':
                queryset = queryset.filter(is_archived=True)
            elif is_archived.lower() == 'false':
                queryset = queryset.filter(is_archived=False)
            
        return queryset

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        resource = self.get_object()
        resource.archive()
        return Response({'status': 'resource archived'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        resource = self.get_object()
        resource.restore()
        return Response({'status': 'resource restored'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        resource = self.get_object()
        history = resource.get_history()
        
        # Serialize history manually
        data = []
        for log in history:
            data.append({
                'id': str(log.id),
                'user': log.user.email if log.user else 'System',
                'action': log.action,
                'changes': log.changes,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp
            })
        return Response(data)

    # Cache response for 5 minutes, varied by Auth header for safety
    @method_decorator(cache_page(60 * 5))
    @method_decorator(vary_on_headers('Authorization', 'Cookie'))
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        user = request.user
        if not user.is_authenticated or not user.role:
            return Response({'error': 'unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Get base queryset filtered by role
        queryset = Resource.objects.all()
        if user.role.name == 'manager':
            queryset = queryset.filter(department=user.department)
        elif user.role.name == 'user':
            queryset = queryset.filter(owner=user)
            
        total = queryset.count()
        active = queryset.filter(status='active', is_archived=False).count()
        inactive = queryset.filter(status='inactive', is_archived=False).count()
        pending = queryset.filter(status='pending', is_archived=False).count()
        archived = queryset.filter(is_archived=True).count()
        
        # Group by category (exclude archived)
        by_category = queryset.filter(is_archived=False).values('category__name').annotate(count=Count('id'))
        
        stats = {
            'total': total,
            'active': active,
            'inactive': inactive,
            'pending': pending,
            'archived': archived,
            'by_category': {item['category__name']: item['count'] for item in by_category if item['category__name']}
        }
        return Response(stats)
