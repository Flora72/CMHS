from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class PatientRegistrationForm(UserCreationForm):
    role = forms.CharField(initial='patient', widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-chiromo-gold'}),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-chiromo-gold'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-chiromo-gold'}),
        }