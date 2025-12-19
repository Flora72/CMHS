from django.db import models
from django.conf import settings


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_patient',
        limit_choices_to={'role': 'patient'}
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments_as_therapist',
        limit_choices_to={'role': 'therapist'}
    )
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appt: {self.patient.username} with {self.therapist.username} on {self.date}"


class SessionLog(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    therapist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='session_logs')

    notes = models.TextField(help_text="Therapist's confidential notes")
    session_date = models.DateField(auto_now_add=True)
    resources = models.FileField(upload_to='therapy_resources/', blank=True, null=True)

    def __str__(self):
        return f"Session: {self.patient.username} - {self.session_date}"


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = models.CharField(max_length=50, unique=True, help_text="M-Pesa Transaction ID")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_code} - {self.amount}"