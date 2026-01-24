from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'specialization','role', 'is_staff']
    list_filter = ['role', 'specialization', 'is_staff']

    fieldsets = UserAdmin.fieldsets + (
        ('Chiromo Profile', {'fields': ('role', 'specialization', 'phone_number')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Chiromo Profile', {'fields': ('role', 'specialization', 'phone_number', 'email')}),
    )


admin.site.register(User, CustomUserAdmin)