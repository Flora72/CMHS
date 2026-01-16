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

CHOICES_FREQ = [
    ('0', 'Not at all'),
    ('1', 'Several days'),
    ('2', 'More than half the days'),
    ('3', 'Nearly every day'),
]

TAILWIND_RADIO = forms.RadioSelect(attrs={'class': 'peer sr-only'})

class DepressionAssessmentForm(forms.Form):
    q1 = forms.ChoiceField(label="1. Little interest or pleasure in doing things?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q2 = forms.ChoiceField(label="2. Feeling down, depressed, or hopeless?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q3 = forms.ChoiceField(label="3. Trouble falling or staying asleep, or sleeping too much?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q4 = forms.ChoiceField(label="4. Feeling tired or having little energy?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q5 = forms.ChoiceField(label="5. Poor appetite or overeating?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)

class AnxietyAssessmentForm(forms.Form):
    q1 = forms.ChoiceField(label="1. Feeling nervous, anxious, or on edge?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q2 = forms.ChoiceField(label="2. Not being able to stop or control worrying?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q3 = forms.ChoiceField(label="3. Worrying too much about different things?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q4 = forms.ChoiceField(label="4. Trouble relaxing?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)
    q5 = forms.ChoiceField(label="5. Being so restless that it is hard to sit still?", choices=CHOICES_FREQ, widget=TAILWIND_RADIO)

class BipolarAssessmentForm(forms.Form):
    CHOICES_YESNO = [('0', 'No'), ('1', 'Yes')]
    q1 = forms.ChoiceField(label="1. Has there ever been a period where you felt so good/hyper that you got into trouble?", choices=CHOICES_YESNO, widget=TAILWIND_RADIO)
    q2 = forms.ChoiceField(label="2. During this time, did you need less sleep than usual?", choices=CHOICES_YESNO, widget=TAILWIND_RADIO)
    q3 = forms.ChoiceField(label="3. Were you more talkative or did you speak faster than usual?", choices=CHOICES_YESNO, widget=TAILWIND_RADIO)
    q4 = forms.ChoiceField(label="4. Did you spend money purely on impulse?", choices=CHOICES_YESNO, widget=TAILWIND_RADIO)
    q5 = forms.ChoiceField(label="5. Did you experience racing thoughts?", choices=CHOICES_YESNO, widget=TAILWIND_RADIO)