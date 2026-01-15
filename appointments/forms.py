from django import forms
from .models import Appointment, SessionLog
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

        # Filter: Only show users who are marked as 'therapist'
        self.fields['therapist'].queryset = User.objects.filter(role='therapist')

        # Label Formatting: Show "Dr. Lastname" if available, otherwise show Username
        self.fields['therapist'].label_from_instance = lambda obj: (
            f"Dr. {obj.last_name} {obj.first_name}" if obj.last_name and obj.first_name
            else f"Dr. {obj.username}"
        )

class SessionLogForm(forms.ModelForm):
    class Meta:
        model = SessionLog
        fields = ['notes', 'resources']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-chiromo-navy focus:border-transparent',
                'rows': 6,
                'placeholder': 'Enter clinical observations, patient progress, and key takeaways...'
            }),
            'resources': forms.FileInput(attrs={
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-chiromo-navy hover:file:bg-blue-100',
            })
        }