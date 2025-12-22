from django.shortcuts import render


# General views
def index(request):
    return render(request,'index.html')

def about(request):
    return render(request,'about.html')

def contact(request):
    return render(request,'contact.html')

# auth related views
def login(request):
    return render(request, 'accounts/login.html')

def signup(request):
    return render(request, 'accounts/register.html')

# dashboard views
def patient_dashboard(request):
    return render(request, 'accounts/dashboard.html')

def therapist_dashboard(request):
    return render(request,'therapist_dashboard.html')