from django.db import models
from django.conf import settings
from accounts.models import User


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # This is the field causing the error!
    MODE_CHOICES = [
        ('online', 'Online (Video Call)'),
        ('physical', 'In-Person (Westlands Center)'),
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_appointments')
    meeting_link = models.URLField(max_length=200, blank=True, null=True, help_text="Zoom/Google Meet link")
    therapist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='therapist_appointments')

    date = models.DateField()
    time = models.TimeField()

    # Ensure this line exists:
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='online')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    meeting_link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} with {self.therapist.username} on {self.date}"

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

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ('great', 'Great'),
        ('okay', 'Okay'),
        ('low', 'Low'),
        ('bad', 'Bad'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moods')
    mood = models.CharField(max_length=10, choices=MOOD_CHOICES)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'created_at')

    def __str__(self):
        return f"{self.patient.username} - {self.mood} - {self.created_at}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.recipient}"

class AssessmentResult(models.Model):
    SEVERITY_CHOICES = [
        ('minimal', 'Minimal'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('moderately_severe', 'Moderately Severe'),
        ('severe', 'Severe'),
    ]

    # NEW FIELD: Which test was this?
    TEST_TYPES = [
        ('depression', 'Depression (PHQ-9)'),
        ('anxiety', 'Anxiety (GAD-7)'),
        ('bipolar', 'Bipolar Disorder'),
        ('substance', 'Substance Use'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments', null=True, blank=True)
    test_type = models.CharField(max_length=20, choices=TEST_TYPES, default='depression')  # <--- New Field
    score = models.IntegerField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.test_type} ({self.score})"