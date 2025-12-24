from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from .forms import PatientRegistrationForm
from django.contrib.auth.decorators import login_required

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
    # Security Check: Kick them out if they are not a therapist
    if request.user.role != 'therapist':
        messages.error(request, "Access denied. Restricted to medical staff.")
        return redirect('dashboard')

    return render(request, 'accounts/therapist_dashboard.html')