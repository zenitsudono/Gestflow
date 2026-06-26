from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser, Role
from .serializers import CustomUserSerializer, RoleSerializer
from .permissions import IsAdmin

# ==========================================
# DRF API ViewSets
# ==========================================

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().select_related('role').order_by('-created_at')
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        # Allow any authenticated user to view/update their own profile
        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdmin()]

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        # PUT/PATCH update profile
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ==========================================
# Web Frontend SSR Views
# ==========================================

def web_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if not email or not password:
            error_message = "Please enter both email and password."
        else:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if not remember_me:
                        request.session.set_expiry(0) # Session expires when browser closes
                    return redirect('dashboard')
                else:
                    error_message = "Your account has been deactivated."
            else:
                error_message = "Invalid email or password."
                
    return render(request, 'login.html', {'error': error_message})

def web_logout(request):
    logout(request)
    return redirect('login')
