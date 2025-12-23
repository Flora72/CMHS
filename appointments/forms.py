from django import forms
from .models import Appointment
from django.contrib.auth import get_user_model

User = get_user_model()

class BookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['therapist', 'date', 'time', 'mode', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-gold'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-gold'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-gold'}),
            'mode': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-gold'}),
            'therapist': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-gold'}),
        }

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        # Filter the dropdown to ONLY show users who are 'therapist'
        self.fields['therapist'].queryset = User.objects.filter(role='therapist')
        self.fields['therapist'].label_from_instance = lambda obj: f"Dr. {obj.last_name} ({obj.first_name})"