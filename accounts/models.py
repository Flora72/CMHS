from django.db import models
from django.contrib.auth.models import AbstractUser


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Specializations"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('therapist', 'Therapist'),
        ('admin', 'Admin'),
    )


    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    is_premium = models.BooleanField(default=False)
    is_high_risk = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.role == 'patient':
            self.specialization = None
        super().save(*args, **kwargs)