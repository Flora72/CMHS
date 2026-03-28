from django.db import models
from django.conf import settings

class Transaction(models.Model):
    # Identifying what kind of payment this is
    TYPE_CHOICES = (
        ('premium', 'Premium Subscription'),
        ('session', 'Clinical Session'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = models.CharField(max_length=20, unique=True, null=True, blank=True)


    checkout_request_id = models.CharField(max_length=100, unique=True, null=True)

    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='session')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_code or 'PENDING'}"


