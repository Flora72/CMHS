from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('therapist', 'Therapist'),
        ('admin', 'Admin'),
    )

    SPECIALIZATION_CHOICES = [
        ('general', 'General Counselor'),
        ('clinical', 'Clinical Psychologist'),
        ('family', 'Family & Marriage Therapist'),
        ('addiction', 'Addiction Specialist'),
        ('child', 'Child & Adolescent Therapist'),
        ('trauma', 'Trauma Specialist'),
    ]

    specialization = models.CharField(
        max_length=50,
        choices=SPECIALIZATION_CHOICES,
        default='general',
        blank=True,
        null=True
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"