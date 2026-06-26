from django.urls import path
from .views import dashboard_view, settings_view, user_management_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('settings/', settings_view, name='settings'),
    path('users/', user_management_view, name='user_management'),
]
