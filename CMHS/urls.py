from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from appointments.views import export_appointments_pdf, preview_appointments_report, preview_payments_report, export_payments_pdf

urlpatterns = [

    # PDF and Preview Routes
    path('admin/reports/appointments/preview/', preview_appointments_report, name='preview_appointments_report'),
    path('admin/reports/payments/preview/', preview_payments_report, name='preview_payments_report'),
    path('admin/reports/appointments/download/', export_appointments_pdf, name='export_appointments_pdf'),
    path('admin/reports/payments/download/', export_payments_pdf, name='export_payments_pdf'),
    path('admin/', admin.site.urls),
    path('', include('cmhsApp.urls')),
    path('', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)