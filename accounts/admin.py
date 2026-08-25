from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Address, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ('email', 'phone', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'phone', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'house', 'is_default')
    list_filter = ('city', 'is_default')
    search_fields = ('user__email', 'user__phone', 'city', 'street')
