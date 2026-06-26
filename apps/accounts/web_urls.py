from django.urls import path
from .views import web_login, web_logout

urlpatterns = [
    path('login/', web_login, name='login'),
    path('logout/', web_logout, name='logout'),
]
