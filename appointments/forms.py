from django import forms
from .models import Appointment, SessionLog
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class BookingForm(forms.ModelForm):
    # 1. Define the professional staggered slots (60 min session + 15 min buffer)
    TIME_SLOTS = [
        ('', '--- Select a Session ---'),
        ('08:00', '08:00 AM - 09:00 AM'),
        ('09:15', '09:15 AM - 10:15 AM'),
        ('10:30', '10:30 AM - 11:30 AM'),
        ('11:45', '11:45 AM - 12:45 PM'),
        # Lunch Break (13:00 - 14:00)
        ('14:00', '02:00 PM - 03:00 PM'),
        ('15:15', '03:15 PM - 04:15 PM'),
    ]

    # Override the time field to use a dropdown instead of a clock
    time = forms.ChoiceField(
        choices=TIME_SLOTS,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-100 rounded-xl focus:border-chiromo-gold focus:ring-0 transition bg-white'
        })
    )

    class Meta:
        model = Appointment
        fields = ['therapist', 'date', 'time', 'mode', 'notes']
        widgets = {
            'therapist': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-100 rounded-xl focus:border-chiromo-gold focus:ring-0 transition appearance-none bg-white',
                'style': 'cursor: pointer;'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border-2 border-gray-100 rounded-xl focus:border-chiromo-gold'
            }),
            'mode': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-100 rounded-xl focus:border-chiromo-gold'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-3 border-2 border-gray-100 rounded-xl focus:border-chiromo-gold',
                'placeholder': 'Briefly describe your reason for visit...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)

        # 2. Filter queryset to only show users with the 'therapist' role
        self.fields['therapist'].queryset = User.objects.filter(role='therapist')

        # 3. Format the dropdown label to show: Dr. Lastname Firstname — (Specialization)
        self.fields['therapist'].label_from_instance = lambda obj: (
            f"Dr. {obj.last_name} {obj.first_name} — ({obj.get_specialization_display()})"
            if obj.last_name and hasattr(obj, 'get_specialization_display') and obj.specialization
            else f"Dr. {obj.last_name} {obj.first_name}" if obj.last_name
            else f"Dr. {obj.username}"
        )

        # 4. Set minimum date to Today to prevent back-dated bookings
        today = timezone.now().date().strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs['min'] = today

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