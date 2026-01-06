from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from .forms import PatientRegistrationForm
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from .models import User

def home(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = PatientRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.role == 'therapist':
                return redirect('therapist_dashboard')
            else:
                return redirect('dashboard')

    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    return render(request, 'accounts/dashboard.html')


# accounts/views.py

@login_required
def therapist_dashboard(request):
    if request.user.role != 'therapist':
        messages.error(request, "Access denied. Restricted to medical staff.")
        return redirect('dashboard')

    return render(request, 'accounts/therapist_dashboard.html')


@login_required
def therapist_appointments(request):
    if request.user.role != 'therapist':
        return redirect('dashboard')

    # Get ALL appointments (not just pending)
    appointments = Appointment.objects.filter(therapist=request.user).order_by('-date', '-time')
    return render(request, 'accounts/therapist_appointments.html', {'appointments': appointments})


@login_required
def therapist_patients(request):
    if request.user.role != 'therapist':
        return redirect('dashboard')

    # Get distinct patients who have booked with this therapist
    patient_ids = Appointment.objects.filter(therapist=request.user).values_list('patient', flat=True).distinct()
    patients = User.objects.filter(id__in=patient_ids)

    return render(request, 'accounts/therapist_patients.html', {'patients': patients})