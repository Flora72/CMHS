from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name='index'),
    path('', views.about, name='about'),
    path('', views.contact, name='contact'),
    path('', views.login, name='login'),
    path('', views.signup, name='signup'),
    path('', views.patient_dashboard, name='patient_dashboard'),
    path('', views.therapist_dashboard, name='therapist_dashboard'),

]