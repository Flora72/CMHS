from django.shortcuts import render


# General views
def index(request):
    return render(request,'index.html')
def login(request):
    return render(request, 'accounts/login.html')

def signup(request):
    return render(request, 'accounts/register.html')

# dashboard views
def patient_dashboard(request):
    return render(request, 'accounts/patient_dashboard.html')

def therapist_dashboard(request):
    return render(request,'accounts/therapist_dashboard.html')