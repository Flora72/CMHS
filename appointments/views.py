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
from cmhsApp.decorators import premium_required
from .models import JournalEntry
from django.http import HttpResponse
from payments.sms_service import send_ussd_sms
import uuid
from django.contrib.auth.decorators import login_required


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
@premium_required
def book_appointment(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user

            # --- VIRTUAL LINK LOGIC ---
            # If the session type is virtual, generate a unique link
            # Assumes your model has a session_type field (Virtual/In-Person)
            if appointment.mode == 'online':
                # Creating a unique Jitsi link for the session
                meeting_id = str(uuid.uuid4())[:8]
                appointment.meeting_link = f"https://meet.jit.si/CMHS-{meeting_id}"
            else:
                appointment.meeting_link = ""

            appointment.save()

            # Updated email notification with the live link
            subject = 'Appointment Confirmed - Chiromo Hospital'
            message = f"""
            Dear {request.user.first_name},
            Your appointment has been successfully booked.

            Therapist: {appointment.therapist.username}
            Date: {appointment.date}
            Time: {appointment.time}
            Session Type: {appointment.mode}
            Meeting Link: {appointment.meeting_link if appointment.meeting_link else 'Physical Session at Branch'}

            Recovery in Dignity.
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
    appointment = get_object_or_404(Appointment, id=appointment_id)
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
@premium_required
def patient_resources(request):
    # 1. Get Private Resources (Your existing logic)
    # We use SessionLog because that is your actual database model
    resources = SessionLog.objects.filter(
        patient=request.user
    ).exclude(resources='').order_by('-session_date')

    # 2. Define Public Resources (New Static Data)
    public_resources = [
        {
            'category': 'General Mental Health',
            'title': 'Understanding Mental Health (WHO)',
            'desc': 'Key facts and determinants of mental well-being.',
            'url': 'https://www.who.int/news-room/fact-sheets/detail/mental-health-strengthening-our-response',
            'type': 'Article',
            'color': 'bg-blue-100 text-blue-600'
        },
        {
            'category': 'Anxiety & Stress',
            'title': 'Grounding Techniques for Panic Attacks',
            'desc': '5-4-3-2-1 Coping technique explained.',
            'url': 'https://www.mayoclinic.org/diseases-conditions/anxiety/diagnosis-treatment/drc-20350967',
            'type': 'Guide',
            'color': 'bg-purple-100 text-purple-600'
        },
        {
            'category': 'Depression',
            'title': 'Coping with Depression',
            'desc': 'Practical steps for self-care and recovery.',
            'url': 'https://www.helpguide.org/articles/depression/coping-with-depression.htm',
            'type': 'Article',
            'color': 'bg-indigo-100 text-indigo-600'
        },
        {
            'category': 'ADHD',
            'title': 'Adult ADHD: Symptoms & Management',
            'desc': 'How to stay organized and focused.',
            'url': 'https://chadd.org/for-adults/overview/',
            'type': 'Article',
            'color': 'bg-orange-100 text-orange-600'
        },
        {
            'category': 'Eating Disorders',
            'title': 'Healthy Relationship with Food',
            'desc': 'Recognizing signs and seeking help.',
            'url': 'https://www.nationaleatingdisorders.org/help-support/contact-helpline',
            'type': 'Support',
            'color': 'bg-pink-100 text-pink-600'
        },
        {
            'category': 'Video Resource',
            'title': 'The Power of Vulnerability - Brené Brown',
            'desc': 'One of the most watched TED talks on connection.',
            'url': 'https://www.ted.com/talks/brene_brown_the_power_of_vulnerability',
            'type': 'Video',
            'color': 'bg-red-100 text-red-600'
        },
    ]

    context = {
        'resources': resources,
        'public_resources': public_resources,
    }

    # Make sure this matches the template file name you are editing
    return render(request, 'appointments/patient_resources.html', context)
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
@premium_required
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
        is_deleted = (msg.body == "This message was deleted")

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
    message.body = "This message was deleted"
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
@login_required
def journal_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        mood = request.POST.get('mood')

        JournalEntry.objects.create(
            patient=request.user,
            title=title,
            content=content,
            mood_rating=mood
        )
        messages.success(request, "Journal entry saved.")
        return redirect('journal')

    entries = JournalEntry.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, 'appointments/journal.html', {'entries': entries})

@csrf_exempt
def ussd_callback(request):
    if request.method == 'POST':
        # Retrieve AT parameters
        text = request.POST.get("text", "").strip()
        phone_number = request.POST.get("phoneNumber")

        text_parts = text.split('*') if text else []
        level = len(text_parts)

        response = ""

        # LEVEL 0: MAIN MENU
        if text == "":
            response = "CON Welcome to CMHS\n1. Book Therapy\n2. Emergency Help\n3. My Account"

        # LEVEL 1: HANDLING MAIN MENU CHOICES
        elif level == 1:
            if text_parts[0] == "1":
                response = "CON Select Service:\n1. Depression Support\n2. Anxiety & Stress\n3. Addiction Recovery"
            elif text_parts[0] == "2":
                response = "CON ⚠️ EMERGENCY\nEnter your location for help:"
            elif text_parts[0] == "3":
                response = "END My Account:\nPlan: Premium\nBal: KES 0.00\nStatus: Active"
            else:
                response = "END Invalid choice. Please dial again."

        # LEVEL 2: HANDLING SERVICE -> TIME SLOTS
        elif level == 2:
            if text_parts[0] == "1":
                response = "CON Select Time Slot:\n1. Today 2:00 PM\n2. Tomorrow 10:00 AM"
            elif text_parts[0] == "2":
                location = text_parts[1]
                response = f"END ALERT RECEIVED!\nAmbulance dispatched to {location}.\nHelp is on the way."

        # LEVEL 3: HANDLING TIME -> BRANCH SELECTION
        elif level == 3:
            if text_parts[0] == "1":
                # Factual Chiromo Hospital Group branches
                response = "CON Select Branch:\n1. Chiromo Lane (Main)\n2. Bustani (Lavington)\n3. Braeside Clinic"

        # LEVEL 4: FINAL CONFIRMATION & SMS TRIGGER
        elif level == 4:
            if text_parts[0] == "1":
                # Extract choices from the session chain
                time_choice = text_parts[2]
                branch_choice = text_parts[3]

                # Logic to map choices to names
                selected_time = "Today 2:00 PM" if time_choice == "1" else "Tomorrow 10:00 AM"

                if branch_choice == "1":
                    selected_branch = "Chiromo Lane (Main)"
                elif branch_choice == "2":
                    selected_branch = "Bustani (Lavington)"
                else:
                    selected_branch = "Braeside Clinic"

                # Final confirmation message for inclusive access
                success_msg = f"BOOKING SUCCESSFUL! Session at {selected_time} in {selected_branch} confirmed. Recovery in Dignity."

                # TRIGGER THE PERSONALIZED SMS
                send_ussd_sms(phone_number, selected_time, selected_branch)

                response = f"END {success_msg}"

        else:
            response = "END Session timed out or invalid input. Please try again."

        return HttpResponse(response, content_type='text/plain')

    return HttpResponse("USSD Gateway Active", content_type='text/plain')
def ussd_simulator(request):
    return render(request, 'ussd_simulator.html')


