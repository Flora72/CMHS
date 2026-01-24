from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import calendar
from datetime import datetime
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from .forms import BookingForm, SessionLogForm
from .models import Appointment, SessionLog, MoodEntry, Message
from django.core.mail import send_mail
from accounts.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



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

            # email notification
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
    else:
        form = BookingForm()

    therapists = User.objects.filter(role='therapist')
    context = {
        'form': form,
        'therapists': therapists
    }

    return render(request, 'appointments/book_appointment.html', context)

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
    # 1. DETERMINE ACTIVE CHAT PARTNER
    chat_partner = None
    if id:
        chat_partner = get_object_or_404(User, id=id)

    # 2. SEND MESSAGE
    if request.method == 'POST' and chat_partner:
        body = request.POST.get('body')
        if body:
            Message.objects.create(
                sender=request.user,
                recipient=chat_partner,
                body=body
            )
            return redirect('inbox_with_id', id=chat_partner.id)

    # 3. GET MESSAGES FOR ACTIVE CHAT
    messages_list = []
    if chat_partner:
        messages_list = Message.objects.filter(
            Q(sender=request.user, recipient=chat_partner) |
            Q(sender=chat_partner, recipient=request.user)
        ).order_by('timestamp')
        Message.objects.filter(recipient=request.user, sender=chat_partner, is_read=False).update(is_read=True)

    # --- NEW PART: FETCH RECENT CONTACTS FOR SIDEBAR ---
    # Get all unique users involved in messages with me
    sent_messages = Message.objects.filter(sender=request.user).values_list('recipient', flat=True)
    received_messages = Message.objects.filter(recipient=request.user).values_list('sender', flat=True)

    # Combine IDs and remove duplicates
    contact_ids = set(list(sent_messages) + list(received_messages))

    # Fetch User objects (exclude self just in case)
    recent_contacts = User.objects.filter(id__in=contact_ids).exclude(id=request.user.id)

    return render(request, 'appointments/inbox.html', {
        'messages_list': messages_list,
        'chat_partner': chat_partner,
        'recent_contacts': recent_contacts,  # <--- Pass this to template
    })


# appointments/views.py

@login_required
def get_chat_messages(request, partner_id):
    partner = get_object_or_404(User, id=partner_id)

    # Fetch and sort
    messages = Message.objects.filter(
        Q(sender=request.user, recipient=partner) |
        Q(sender=partner, recipient=request.user)
    ).order_by('timestamp')

    # Mark as read
    Message.objects.filter(sender=partner, recipient=request.user, is_read=False).update(is_read=True)

    data = []
    for msg in messages:
        # LOGIC: If I sent it, and it's not already deleted, I can edit/delete it.
        # No time limits anymore.
        is_owner = (msg.sender == request.user)
        is_deleted = (msg.body == "🚫 This message was deleted")

        data.append({
            'id': msg.id,
            'sender': 'me' if is_owner else 'partner',
            'body': msg.body,
            'timestamp': timezone.localtime(msg.timestamp).strftime("%H:%M"),
            'can_edit': is_owner and not is_deleted,  # Always True for owner
            'can_delete': is_owner and not is_deleted,  # Always True for owner
            'is_deleted': is_deleted
        })

    return JsonResponse({'messages': data})


@login_required
def delete_message(request, msg_id):
    # Verify ownership ONLY
    message = get_object_or_404(Message, id=msg_id, sender=request.user)

    # Soft Delete
    message.body = "🚫 This message was deleted"
    message.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})

    return redirect('inbox_with_id', id=message.recipient.id)


@login_required
@csrf_exempt
def edit_message(request, msg_id):
    # Verify ownership ONLY
    message = get_object_or_404(Message, id=msg_id, sender=request.user)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_body = data.get('body')
        except:
            new_body = request.POST.get('body')

        if new_body:
            message.body = new_body
            message.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})

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

def take_assessment(request):
    if request.method == 'POST':
        # assessment scores categorization

        # Anxiety Questions (Q1-Q3)
        a1 = int(request.POST.get('q1', 0))
        a2 = int(request.POST.get('q2', 0))
        a3 = int(request.POST.get('q3', 0))
        anxiety_total = a1 + a2 + a3

        # Depression Questions (Q4-Q6)
        d1 = int(request.POST.get('q4', 0))
        d2 = int(request.POST.get('q5', 0))
        d3 = int(request.POST.get('q6', 0))
        depression_total = d1 + d2 + d3

        # Addiction Questions (Q7-Q9)
        s1 = int(request.POST.get('q7', 0))
        s2 = int(request.POST.get('q8', 0))
        s3 = int(request.POST.get('q9', 0))
        substance_total = s1 + s2 + s3

        result_title = "General Mental Wellness"
        result_desc = "Your responses suggest you are coping well, but regular check-ins are healthy."
        recommended_specialty = 'general'

        # High Substance Risk (Priority)
        if substance_total >= 5:
            result_title = "Risk of Substance Use Disorder"
            result_desc = "Your responses indicate signs of dependency or substance misuse. Professional support is highly recommended to manage this safely."
            recommended_specialty = 'addiction'

        # High Depression Risk
        elif depression_total >= 6:
            result_title = "Signs of Moderate to Severe Depression"
            result_desc = "You reported frequent low mood and loss of interest. A Clinical Psychologist can help you develop coping strategies."
            recommended_specialty = 'clinical'

        # High Anxiety Risk
        elif anxiety_total >= 6:
            result_title = "High Anxiety & Stress Levels"
            result_desc = "You seem to be experiencing significant worry or inability to relax. A therapist can help with stress management techniques."
            recommended_specialty = 'general'

        # Moderate Mix
        elif anxiety_total >= 4 or depression_total >= 4:
            result_title = "Mild Emotional Distress"
            result_desc = "You are experiencing some symptoms of stress or low mood. Early intervention with a counselor can prevent this from worsening."
            recommended_specialty = 'general'

        # --- 3. SEND TO RESULT PAGE ---
        context = {
            'result_title': result_title,
            'result_desc': result_desc,
            'specialty': recommended_specialty,
            'score_a': anxiety_total,  # Optional: Show them their breakdown
            'score_d': depression_total,
            'score_s': substance_total,
        }
        return render(request, 'appointments/public_result.html', context)

    return render(request, 'appointments/take_assessment.html')

@login_required
@csrf_exempt
def send_chat_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        body = data.get('body')

        recipient = get_object_or_404(User, id=recipient_id)

        Message.objects.create(
            sender=request.user,
            recipient=recipient,
            body=body
        )
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)