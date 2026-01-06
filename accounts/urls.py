from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('therapist-dashboard/appointments/', views.therapist_appointments, name='therapist_appointments'),
    path('therapist-dashboard/patients/', views.therapist_patients, name='therapist_patients'),

    path('therapist-dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout')

]