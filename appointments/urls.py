from django.urls import path
from . import views

urlpatterns = [
    path('calendar/', views.calendar_view, name='calendar'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('session/log/<int:appointment_id>/', views.log_session, name='log_session'),
    path('patient/resources/', views.patient_resources, name='patient_resources'),
    path('mood/log/<str:mood_value>/', views.log_mood, name='log_mood'),
    path('my-appointments/', views.patient_appointments, name='patient_appointments'),
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:id>/', views.inbox, name='inbox_with_id'),
    path('message/delete/<int:msg_id>/', views.delete_message, name='delete_message'),
    path('message/edit/<int:msg_id>/', views.edit_message, name='edit_message'),
    path('cancel/<int:id>/', views.cancel_appointment, name='cancel_appointment'),
    path('assessment/', views.assessment_hub, name='assessment_hub'),
    path('take_assessment/', views.take_assessment, name='take_assessment'),
    path('api/get-messages/<int:partner_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('api/send-message/', views.send_chat_message, name='send_chat_message'),
    path('journal/', views.journal_view, name='journal'),
    path('ussd-demo/', views.ussd_simulator, name='ussd_simulator'),
    path('ussd-callback/', views.ussd_callback, name='ussd_callback'),
]