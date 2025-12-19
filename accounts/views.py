from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import PatientRegistrationForm


def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})