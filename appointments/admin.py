from django.contrib import admin
from .models import Appointment, SessionLog, Payment

# Registering these models makes them visible in the admin dashboard
admin.site.register(Appointment)
admin.site.register(SessionLog)
admin.site.register(Payment)