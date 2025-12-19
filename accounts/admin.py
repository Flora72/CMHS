from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# This allows you to see your Custom User model in the admin panel
admin.site.register(User, UserAdmin)