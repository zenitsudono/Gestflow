from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import Http404

from apps.resources.models import Resource, Category
from apps.audit.models import AuditLog
from apps.accounts.models import CustomUser, Role

@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    if not user.role:
        return redirect('login')

    # Base querysets with RBAC
    resources_qs = Resource.objects.all()
    audit_qs = AuditLog.objects.all().select_related('user')

    if user.role.name == 'manager':
        resources_qs = resources_qs.filter(department=user.department)
        audit_qs = audit_qs.filter(user__department=user.department)
    elif user.role.name == 'user':
        resources_qs = resources_qs.filter(owner=user)
        audit_qs = audit_qs.filter(user=user)

    # Calculate KPI Card Counts
    total_resources = resources_qs.filter(is_archived=False).count()
    active_resources = resources_qs.filter(status='active', is_archived=False).count()
    pending_resources = resources_qs.filter(status='pending', is_archived=False).count()
    archived_resources = resources_qs.filter(is_archived=True).count()

    # Get recent logs for the activity feed (limit 5)
    recent_activities = audit_qs.order_by('-timestamp')[:5]

    # Chart.js Data: Resources by Category
    category_counts = resources_qs.filter(is_archived=False).values('category__name').annotate(count=Count('id'))
    chart_categories = [item['category__name'] for item in category_counts if item['category__name']]
    chart_values = [item['count'] for item in category_counts if item['category__name']]

    # Chart.js Data: Resources status breakdown
    status_counts = resources_qs.filter(is_archived=False).values('status').annotate(count=Count('id'))
    status_map = {
        'active': 'En cours',
        'inactive': 'Résolue',
        'pending': 'En attente'
    }
    status_labels = [status_map.get(item['status'], item['status'].capitalize()) for item in status_counts]
    status_values = [item['count'] for item in status_counts]

    context = {
        'total_resources': total_resources,
        'active_resources': active_resources,
        'pending_resources': pending_resources,
        'archived_resources': archived_resources,
        'recent_activities': recent_activities,
        'chart_categories': chart_categories,
        'chart_values': chart_values,
        'status_labels': status_labels,
        'status_values': status_values,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def settings_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.bio = request.POST.get('bio', '')
        
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
            
        password = request.POST.get('password')
        if password:
            user.set_password(password)
            
        user.save()
        messages.success(request, 'Profile updated successfully!')
        if password:
            # Re-authenticate after password change
            return redirect('login')
        return redirect('settings')
        
    return render(request, 'settings.html', {'departments': dict(user.DEPARTMENT_CHOICES)})

@login_required(login_url='login')
def user_management_view(request):
    user = request.user
    if not user.role or user.role.name != Role.ADMIN:
        raise Http404("You do not have permission to access this page.")

    users = CustomUser.objects.all().select_related('role').order_by('-created_at')
    roles = Role.objects.all()

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        user_id = request.POST.get('user_id')
        target_user = get_object_or_404(CustomUser, pk=user_id)

        if action_type == 'update_role':
            role_id = request.POST.get('role')
            department = request.POST.get('department')
            if role_id:
                target_user.role_id = role_id
            if department:
                target_user.department = department
            target_user.save()
            messages.success(request, f'User {target_user.email} updated successfully.')
        elif action_type == 'delete_user':
            if target_user == user:
                messages.error(request, "You cannot delete yourself.")
            else:
                target_user.delete()
                messages.success(request, f'User {target_user.email} deleted successfully.')
        return redirect('user_management')

    return render(request, 'users/management.html', {
        'users_list': users,
        'roles_list': roles,
        'departments': dict(user.DEPARTMENT_CHOICES)
    })
