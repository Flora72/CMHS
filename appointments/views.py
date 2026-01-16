from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import calendar
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from .forms import BookingForm, SessionLogForm, DepressionAssessmentForm, AnxietyAssessmentForm, BipolarAssessmentForm
from .models import Appointment, SessionLog, MoodEntry, Message, User, AssessmentResult
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

@login_required
def log_session(request, appointment_id):
    # 1. Get the appointment
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # 2. Security: Ensure the logged-in user is the assigned therapist
    if request.user != appointment.therapist:
        messages.error(request, "You are not authorized to log this session.")
        return redirect('therapist_dashboard')

    # 3. Handle Form Submission
    if request.method == 'POST':
        form = SessionLogForm(request.POST, request.FILES)  # <--- FILES is important for uploads!
        if form.is_valid():
            session_log = form.save(commit=False)

            # Link everything together
            session_log.appointment = appointment
            session_log.therapist = request.user
            session_log.patient = appointment.patient
            session_log.save()

            # 4. Mark Appointment as Completed
            appointment.status = 'completed'
            appointment.save()

            messages.success(request, "Session logged successfully.")
            return redirect('therapist_appointments')
    else:
        form = SessionLogForm()

    return render(request, 'appointments/log_session.html', {
        'form': form,
        'appointment': appointment
    })

@login_required
def patient_resources(request):
    # logs for the patients that actually have a file uploaded
    resources = SessionLog.objects.filter(
        patient=request.user
    ).exclude(resources='').order_by('-session_date')

    return render(request, 'appointments/patient_resources.html', {'resources': resources})

@login_required
def patient_appointments(request):
    # all appointments for the patients are fetched
    appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')

    return render(request, 'appointments/patient_appointments.html', {'appointments': appointments})


@login_required
def log_mood(request, mood_value):
    # Check if they already logged today
    today = timezone.now().date()
    existing_entry = MoodEntry.objects.filter(patient=request.user, created_at=today).exists()

    if not existing_entry:
        MoodEntry.objects.create(patient=request.user, mood=mood_value)
        messages.success(request, "Mood logged successfully!")
    else:
        messages.info(request, "You have already logged your mood for today.")

    return redirect('dashboard')


@login_required
def inbox(request, id=None):
    # 1. DETERMINE THE CHAT PARTNER
    chat_partner = None

    if id:
        # If an ID is passed (e.g., Doctor clicked "Message" on a patient)
        chat_partner = get_object_or_404(User, id=id)

    else:
        # If no ID, try to find the most recent conversation
        last_msg = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).order_by('-timestamp').last()

        if last_msg:
            chat_partner = last_msg.recipient if last_msg.sender == request.user else last_msg.sender

    # If still no partner (New account), handle gracefully
    if not chat_partner:
        if request.user.role == 'patient':
            # Fallback for patient: Find their therapist
            last_appt = Appointment.objects.filter(patient=request.user).first()
            if last_appt:
                chat_partner = last_appt.therapist
            else:
                messages.warning(request, "Book an appointment to start chatting!")
                return redirect('dashboard')
        else:
            messages.info(request, "Select a patient to start messaging.")
            return redirect('therapist_patients')

    # 2. HANDLE SENDING MESSAGES
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            Message.objects.create(
                sender=request.user,
                recipient=chat_partner,
                body=body
            )
            return redirect('inbox_with_id', id=chat_partner.id)  # Reload with specific ID

    # 3. GET CHAT HISTORY
    messages_list = Message.objects.filter(
        Q(sender=request.user, recipient=chat_partner) |
        Q(sender=chat_partner, recipient=request.user)
    ).order_by('timestamp')

    # Mark as read
    Message.objects.filter(recipient=request.user, sender=chat_partner, is_read=False).update(is_read=True)

    return render(request, 'appointments/inbox.html', {
        'messages_list': messages_list,
        'chat_partner': chat_partner
    })


@login_required
def delete_message(request, msg_id):
    # Only allow deletion if the logged-in user is the sender
    message = get_object_or_404(Message, id=msg_id, sender=request.user)

    # Store the partner's ID to redirect back to the chat
    partner_id = message.recipient.id
    message.delete()

    messages.success(request, "Message unsent.")
    return redirect('inbox_with_id', id=partner_id)


@login_required
def edit_message(request, msg_id):
    message = get_object_or_404(Message, id=msg_id, sender=request.user)

    if request.method == 'POST':
        new_body = request.POST.get('body')
        if new_body:
            message.body = new_body
            message.save()
            messages.success(request, "Message edited.")

    return redirect('inbox_with_id', id=message.recipient.id)

@login_required
def cancel_appointment(request, id):

    appointment = get_object_or_404(Appointment, id=id, patient=request.user)

    if appointment.status == 'pending':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, "Appointment cancelled successfully.")
    else:
        messages.error(request, "You can only cancel pending appointments.")

    return redirect('patient_appointments')

def assessment_hub(request):
    return render(request, 'appointments/assessment_hub.html')

def take_assessment(request, test_type):
    if test_type == 'anxiety':
        FormClass = AnxietyAssessmentForm
        title = "Anxiety Screening (GAD-7)"
    elif test_type == 'bipolar':
        FormClass = BipolarAssessmentForm
        title = "Bipolar Disorder Screening"
    else:
        FormClass = DepressionAssessmentForm
        title = "Depression Screening (PHQ-9)"

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            total_score = 0
            for field in form.cleaned_data:
                total_score += int(form.cleaned_data[field])

            # Simple logic for Demo purposes (Real medical logic is complex)
            if total_score <= 4: severity = 'minimal'
            elif total_score <= 9: severity = 'mild'
            elif total_score <= 14: severity = 'moderate'
            else: severity = 'severe'

            if request.user.is_authenticated:
                AssessmentResult.objects.create(
                    patient=request.user,
                    test_type=test_type, # Save which test it was
                    score=total_score,
                    severity=severity
                )
                return redirect('dashboard')
            else:
                # Guest Logic
                request.session['guest_score'] = total_score
                request.session['guest_severity'] = severity
                request.session['guest_test_type'] = title
                return redirect('public_result')

    else:
        form = FormClass()

    return render(request, 'appointments/take_assessment.html', {
        'form': form,
        'title': title
    })

def public_result(request):
    score = request.session.get('guest_score')
    severity = request.session.get('guest_severity')

    if score is None:
        return redirect('assessment_hub')

    # CLEAN THE TEXT HERE:
    if severity:
        severity_display = severity.replace('_', ' ') # Replaces underscore with space
    else:
        severity_display = "Unknown"

    return render(request, 'appointments/public_result.html', {
        'score': score,
        'severity': severity_display, # Pass the clean version
    })