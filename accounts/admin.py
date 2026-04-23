from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Specialization
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- 1. PDF Export Action ---
def export_customers_pdf(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Customer_Demographics_Report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Header Section
    elements.append(Paragraph("Online CMHS", styles['Title']))
    elements.append(Paragraph("Patient Demographics Report", styles['Heading2']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    # Table Data
    data = [['Username', 'Email', 'Role', 'High Risk', 'Premium']]

    for user in queryset:
        data.append([
            user.username,
            user.email,
            user.role,
            "Yes" if user.is_high_risk else "No",
            "Yes" if user.is_premium else "No"
        ])

    # Executive Styling
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00183E")),  # Navy Header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    elements.append(table)
    doc.build(elements)
    return response

export_customers_pdf.short_description = "Generate Customer PDF Report"

# --- 2. Specialization Admin ---
@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# --- 3. Custom User Admin ---
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # This list_display must match the methods/fields exactly to prevent line 86 errors
    list_display = ('username', 'email', 'role', 'display_specialization', 'is_high_risk', 'is_staff')

    # FIX: Updated logic to handle the new ForeignKey relationship (Object vs String)
    def display_specialization(self, obj):
        if obj.role == 'therapist' and obj.specialization:
            return obj.specialization.name # Returns the 'name' from the related model
        return "—"

    display_specialization.short_description = 'Professional Specialization'

    list_filter = ('role', 'is_high_risk', 'specialization', 'is_staff')
    search_fields = ('username', 'email', 'phone_number')
    actions = [export_customers_pdf]

    # Added clinical fields to the standard User Admin layout
    fieldsets = UserAdmin.fieldsets + (
        ('Chiromo Clinical Profile', {
            'fields': ('role', 'specialization', 'phone_number', 'is_high_risk', 'is_premium')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Chiromo Clinical Profile', {
            'fields': ('role', 'specialization', 'phone_number', 'email')
        }),
    )

    # Dashboard Statistics logic
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_high_risk'] = User.objects.filter(is_high_risk=True).count()
        extra_context['total_therapists'] = User.objects.filter(role='therapist').count()
        return super().changelist_view(request, extra_context=extra_context)