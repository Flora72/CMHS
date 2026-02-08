from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from .forms import PatientRegistrationForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment, MoodEntry, Message
from datetime import date
from .models import User
from django.utils import timezone
from django.contrib import messages
def home(request):
    return render(request, 'index.html')
def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')

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
    today = timezone.now().date()

    # Check if mood logged today
    todays_mood = MoodEntry.objects.filter(patient=user, created_at=today).first()
    unread_count = Message.objects.filter(recipient=user, is_read=False).count()

    context = {
        'todays_mood': todays_mood,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/patient_dashboard.html', context)
@login_required
def therapist_dashboard(request):
    # 1. Security Check
    if request.user.role != 'therapist':
        messages.error(request, "Access denied. Restricted to medical staff.")
        return redirect('dashboard')

    # 2. Get the specific data for THIS therapist
    pending_requests = Appointment.objects.filter(
        therapist=request.user,
        status='pending'
    ).order_by('date', 'time')

    # 3. Calculate the counts
    pending_count = pending_requests.count()

    todays_count = Appointment.objects.filter(
        therapist=request.user,
        date=date.today(),
        status='confirmed'
    ).count()

    # Count distinct patients assigned to this therapist
    total_patients = Appointment.objects.filter(
        therapist=request.user
    ).values('patient').distinct().count()

    # 4. specific context dictionary
    context = {
        'pending_requests': pending_requests,
        'pending_count': pending_count,
        'todays_count': todays_count,
        'total_patients': total_patients,
    }

    return render(request, 'accounts/therapist_dashboard.html', context)
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

@login_required
def approve_appointment(request, pk):
    # 1. Get the specific appointment by its ID (pk)
    appointment = get_object_or_404(Appointment, pk=pk)

    # 2. Security Check: Ensure only the assigned therapist can approve it
    if request.user != appointment.therapist:
        messages.error(request, "You are not authorized to manage this appointment.")
        return redirect('therapist_dashboard')

    # 3. Update the status
    appointment.status = 'confirmed'
    appointment.save()

    messages.success(request, f"Appointment with {appointment.patient.first_name} confirmed!")
    return redirect('therapist_dashboard')
@login_required
def decline_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user != appointment.therapist:
        messages.error(request, "You are not authorized to manage this appointment.")
        return redirect('therapist_dashboard')

    appointment.status = 'cancelled'
    appointment.save()

    messages.warning(request, "Appointment request declined.")
    return redirect('therapist_dashboard')

@login_required
def settings_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile details updated successfully!")
            return redirect('settings')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/settings.html', {'form': form})

@login_required
def toggle_risk(request, user_id):
    # Security: Only therapists can do this
    if request.user.role != 'therapist':
        return redirect('dashboard')

    patient = User.objects.get(pk=user_id)

    # Flip the status (True -> False, or False -> True)
    patient.is_high_risk = not patient.is_high_risk
    patient.save()

    status_msg = "High Risk" if patient.is_high_risk else "Normal Risk"
    messages.warning(request, f"Patient flagged as {status_msg}.")

    return redirect('therapist_patients')