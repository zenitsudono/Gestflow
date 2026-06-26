from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.ok if hasattr(admin.site, 'ok') else admin.site.urls),

    # Web Template Frontend (SSR)
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.web_urls')),
    path('resources/', include('apps.resources.web_urls')),

    # API Authentication Endpoints
    path('api/v1/auth/token/', TokenObtainPairView.as_callable() if hasattr(TokenObtainPairView, 'as_callable') else TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_callable() if hasattr(TokenRefreshView, 'as_callable') else TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/token/blacklist/', TokenBlacklistView.as_callable() if hasattr(TokenBlacklistView, 'as_callable') else TokenBlacklistView.as_view(), name='token_blacklist'),

    # API Endpoints
    path('api/v1/users/', include('apps.accounts.api_urls')),
    path('api/v1/resources/', include('apps.resources.api_urls')),
    path('api/v1/documents/', include('apps.documents.api_urls')),
    path('api/v1/notifications/', include('apps.notifications.api_urls')),

    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
