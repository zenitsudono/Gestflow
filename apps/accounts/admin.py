from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Role

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'role', 'department', 'phone', 'is_staff', 'is_active')
    list_filter = ('role', 'department', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'avatar', 'phone', 'bio', 'department', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Role)
