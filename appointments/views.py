from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import calendar
from datetime import datetime
from django.contrib import messages
from .forms import BookingForm
from .models import Appointment
from django.core.mail import send_mail


@login_required
def calendar_view(request):
    today = datetime.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    appointments = Appointment.objects.filter(
        patient=request.user,
        date__year=year,
        date__month=month
    )

    appointments_by_day = {}
    for appt in appointments:
        day = appt.date.day
        if day not in appointments_by_day:
            appointments_by_day[day] = []
        appointments_by_day[day].append(appt)

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    month_name = calendar.month_name[month]

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_days': month_days,
        'appointments_by_day': appointments_by_day,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': today,
    }

    return render(request, 'appointments/calendar.html', context)
@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.save()

            # --- SEND EMAIL CODE ---
            subject = 'Appointment Confirmed - Chiromo Hospital'
            message = f"""
            Dear {request.user.first_name},

            Your appointment has been successfully booked.

            Therapist: {appointment.therapist.username}
            Date: {appointment.date}
            Time: {appointment.time}
            Link: {appointment.meeting_link or 'Pending'}

            Thank you for choosing Chiromo.
            """
            from_email = 'noreply@chiromo.com'
            recipient_list = [request.user.email]

            send_mail(subject, message, from_email, recipient_list, fail_silently=True)

            messages.success(request, 'Your session has been booked successfully! Check your email.')
            return redirect('dashboard')

    # --- THIS ELSE BLOCK WAS MISSING ---
    else:
        form = BookingForm()
    # -----------------------------------

    return render(request, 'appointments/book_appointment.html', {'form': form})