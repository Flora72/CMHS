from django.contrib import admin
from payments.models import Transaction
from accounts.models import Specialization
from .models import Appointment, SessionLog
from django.db.models import Sum



admin.site.register(SessionLog)
admin.site.register(Specialization)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'therapist', 'date', 'status')
    list_filter = ('status', 'date', 'therapist')
    search_fields = ('patient__username', 'therapist__username', 'notes')


def custom_admin_index(request, extra_context=None):
    extra_context = extra_context or {}

    total_apps = Appointment.objects.count()

    ussd_count = Appointment.objects.filter(status__iexact='Pending').count()

    actual_revenue = Transaction.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

    formatted_revenue = "{:,.2f}".format(actual_revenue)

    extra_context['ussd_intake'] = ussd_count
    extra_context['web_intake'] = total_apps - ussd_count

    extra_context['total_appointments'] = total_apps
    extra_context['pending_sessions'] = ussd_count
    extra_context['total_revenue'] = formatted_revenue

    return original_index(request, extra_context=extra_context)

original_index = admin.site.index
admin.site.index = custom_admin_index



