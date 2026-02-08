from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # 1. What columns to show in the list
    list_display = ('user', 'phone_number', 'amount', 'status', 'transaction_code', 'timestamp')

    # 2. Add sidebar filters (useful for reports)
    list_filter = ('status', 'timestamp')

    # 3. Add a Search Bar (Search by Username, Phone, or M-Pesa Code)
    search_fields = ('user__username', 'phone_number', 'transaction_code', 'checkout_request_id')

    # 4. Make critical fields read-only so admins don't tamper with receipts
    readonly_fields = ('timestamp', 'checkout_request_id')

    # 5. Default ordering (Newest first)
    ordering = ('-timestamp',)

    # Bonus: Colored Status indicators (Optional visual flair)
    def get_list_display_links(self, request, list_display):
        return ('user', 'transaction_code')