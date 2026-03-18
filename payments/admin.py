from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # Financial Audit Trail
    list_display = ('transaction_code', 'user', 'phone_number', 'amount', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('transaction_code', 'phone_number', 'user__username')
    readonly_fields = ('timestamp', 'transaction_code', 'checkout_request_id')

    ordering = ('-timestamp',)