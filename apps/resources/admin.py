from django.contrib import admin
from .models import Resource, Category

class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'owner', 'department', 'status', 'is_archived', 'created_at')
    list_filter = ('category', 'status', 'is_archived', 'department')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Resource, ResourceAdmin)
admin.site.register(Category)
