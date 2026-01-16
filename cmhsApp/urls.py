from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.index, name='index'),
    path('', views.about, name='about'),
    path('', views.contact, name='contact'),
    path('', views.login, name='login'),
    path('', views.signup, name='signup'),
    path('', views.patient_dashboard, name='patient_dashboard'),
    path('', views.therapist_dashboard, name='therapist_dashboard'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/password-change/done/'
    ), name='change_password'),

    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

]