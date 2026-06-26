from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Resource, Category

@login_required(login_url='login')
def resource_list(request):
    user = request.user
    if not user.role:
        return redirect('login')
        
    show_archived = request.GET.get('archived', 'false').lower() == 'true'
        
    # Queryset filtering based on Role-Based Access Control
    queryset = Resource.objects.filter(is_archived=show_archived).select_related('category', 'owner')
    if user.role.name == 'manager':
        queryset = queryset.filter(department=user.department)
    elif user.role.name == 'user':
        queryset = queryset.filter(owner=user)
        
    # Apply user-submitted filters
    search_query = request.GET.get('search', '').strip()
    category_query = request.GET.get('category', '').strip()
    status_query = request.GET.get('status', '').strip()
    
    if search_query:
        queryset = queryset.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
    if category_query:
        queryset = queryset.filter(category_id=category_query)
    if status_query:
        queryset = queryset.filter(status=status_query)
        
    categories = Category.objects.all()
    return render(request, 'resources/list.html', {
        'resources': queryset,
        'categories': categories,
        'departments': dict(user.DEPARTMENT_CHOICES),
        'show_archived': show_archived,
    })

@login_required(login_url='login')
def resource_detail(request, pk):
    user = request.user
    if not user.role:
        return redirect('login')
        
    resource = get_object_or_404(Resource, pk=pk)
    
    # Check permissions
    if user.role.name == 'manager' and resource.department != user.department:
        return redirect('resource_list')
    elif user.role.name == 'user' and resource.owner != user:
        return redirect('resource_list')
        
    return render(request, 'resources/detail.html', {
        'resource': resource
    })
