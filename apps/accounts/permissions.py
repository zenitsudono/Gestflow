from rest_framework import permissions
from .models import Role

class IsAdmin(permissions.BasePermission):
    """
    Allows access only to Admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role and request.user.role.name == Role.ADMIN

class IsManager(permissions.BasePermission):
    """
    Allows access only to Manager users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role and request.user.role.name == Role.MANAGER

class IsAdminOrManager(permissions.BasePermission):
    """
    Allows access to Admin or Manager users.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.role:
            return False
        return request.user.role.name in [Role.ADMIN, Role.MANAGER]

class ResourcePermission(permissions.BasePermission):
    """
    Custom permission for GestiFlow Resources.
    - Admin: View/Create/Edit/Delete all
    - Manager: View/Create/Edit own dept, Edit own resource, Delete ✗
    - User: View/Create/Edit own, Delete ✗
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.role:
            return False
        
        # All authenticated roles can list/retrieve or create
        if request.method in permissions.SAFE_METHODS or request.method == 'POST':
            return True
            
        # Only admin can delete
        if request.method == 'DELETE':
            return request.user.role.name == Role.ADMIN
            
        # Edit/Update (PUT/PATCH): Allow users to hit the endpoint, but let has_object_permission decide
        return True

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.role.name == Role.ADMIN:
            return True
            
        # Safe methods (Viewing/Retrieving)
        if request.method in permissions.SAFE_METHODS:
            if request.user.role.name == Role.MANAGER:
                # Manager can view if in same department
                return obj.department == request.user.department
            # User can only view their own
            return obj.owner == request.user

        # Write methods (PUT/PATCH)
        # Edit own resource is allowed for both Manager and User
        return obj.owner == request.user
