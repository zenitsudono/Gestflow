from django.contrib import admin
from .models import Notification

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('title', 'message', 'recipient__email')
    ordering = ('-created_at',)

admin.site.register(Notification, NotificationAdmin)
