from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Resource, Category

@login_required(login_url='login')
def resource_list(request):
    user = request.user
    if not user.role:
        return redirect('login')
        
    # Queryset filtering based on Role-Based Access Control
    queryset = Resource.objects.filter(is_archived=False).select_related('category', 'owner')
    if user.role.name == 'manager':
        queryset = queryset.filter(department=user.department)
    elif user.role.name == 'user':
        queryset = queryset.filter(owner=user)
        
    categories = Category.objects.all()
    return render(request, 'resources/list.html', {
        'resources': queryset,
        'categories': categories,
        'departments': dict(user.DEPARTMENT_CHOICES)
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
