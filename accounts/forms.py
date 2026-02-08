from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class PatientRegistrationForm(UserCreationForm):
    role = forms.CharField(initial='patient', widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'role']

    def __init__(self, *args, **kwargs):
        super(PatientRegistrationForm, self).__init__(*args, **kwargs)


        for field_name in self.fields:
            self.fields[field_name].widget.attrs[
                'class'] = 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-chiromo-gold'


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-navy'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-navy'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-chiromo-navy'}),
        }

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['phone_number'].widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-chiromo-gold focus:border-transparent outline-none transition',
                'placeholder': '07...'
            })


class TherapistRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'specialization']  # Added specialization

    # Optional: Style the dropdown
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialization'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-chiromo-gold'
        })