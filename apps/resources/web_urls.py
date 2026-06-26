from django.urls import path
from .web_views import resource_list, resource_detail

urlpatterns = [
    path('', resource_list, name='resource_list'),
    path('<uuid:pk>/', resource_detail, name='resource_detail'),
]
