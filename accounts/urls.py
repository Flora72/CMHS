from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('therapist-dashboard/appointments/', views.therapist_appointments, name='therapist_appointments'),
    path('therapist-dashboard/patients/', views.therapist_patients, name='therapist_patients'),
    path('appointments/approve/<int:pk>/', views.approve_appointment, name='approve_appointment'),
    path('appointment/decline/<int:pk>/', views.decline_appointment, name='decline_appointment'),
    path('therapist-dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patient/<int:user_id>/toggle-risk/', views.toggle_risk, name='toggle_risk'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout')

]