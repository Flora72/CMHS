from django.urls import path
from . import views

urlpatterns = [
    path('calendar/', views.calendar_view, name='calendar'),
    path('book/', views.book_appointment, name='book_appointment'),
]