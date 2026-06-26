from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, RoleViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'', CustomUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
