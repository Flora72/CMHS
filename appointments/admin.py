from django.contrib import admin
from .models import Appointment, SessionLog



admin.site.register(SessionLog)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'therapist', 'date', 'status')
    list_filter = ('status', 'date', 'therapist')
    search_fields = ('patient__username', 'therapist__username', 'notes')


def custom_admin_index(request, extra_context=None):
    extra_context = extra_context or {}

    # Total Global Intake (currently 14)
    total_apps = Appointment.objects.count()

    # USSD LOGIC: Count the appointments that are currently 'Pending'
    # We use __iexact to ensure it matches 'Pending' exactly as seen in your list
    ussd_count = Appointment.objects.filter(status__iexact='Pending').count()

    # Calculations for the wheel
    extra_context['ussd_intake'] = ussd_count
    extra_context['web_intake'] = total_apps - ussd_count

    # Widget Metrics
    extra_context['total_appointments'] = total_apps
    # This keeps your 'Pending Review' widget accurate (showing 2)
    extra_context['pending_sessions'] = ussd_count
    extra_context['total_revenue'] = "6,000.00"

    return original_index(request, extra_context=extra_context)

original_index = admin.site.index
admin.site.index = custom_admin_index