from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import calendar
from datetime import date, time, timedelta
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
from payments.sms_service import send_ussd_sms
import uuid
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from .models import Appointment
from payments.models import Transaction



# ---------------------------------------------
# ADMIN SIDE VIEWS (PDF GENERATION)
# ---------------------------------------------
def preview_appointments_report(request):
    data = Appointment.objects.all().order_by('-date')
    return render(request, 'admin/report_preview.html', {
        'title': 'Clinical Appointment Summary',
        'data': data,
        'type': 'clinical',
        'export_url': 'export_appointments_pdf'
    })


def preview_payments_report(request):
    data = Transaction.objects.filter(status='completed').order_by('-timestamp')
    return render(request, 'admin/report_preview.html', {
        'title': 'Financial Transaction Summary',
        'data': data,
        'type': 'financial',
        'export_url': 'export_payments_pdf'
    })


# --- PDF GENERATION ENGINE ---
def generate_pdf(filename, title, headers, data):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Chiromo Mental Health System", styles['Title']))
    elements.append(Paragraph(title, styles['Heading2']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    table_data = [headers] + data
    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00183E")),  # Navy
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    doc.build(elements)
    return response


def export_appointments_pdf(request):
    apps = Appointment.objects.all()
    data = [[a.patient.username, a.therapist.username, a.date.strftime('%Y-%m-%d'), a.status] for a in apps]
    return generate_pdf("Clinical_Report", "Clinical Appointment Summary", ['Patient', 'Therapist', 'Date', 'Status'],
                        data)


def export_payments_pdf(request):
    trans = Transaction.objects.filter(status='completed')
    data = [[t.transaction_id, f"KES {t.amount}", t.timestamp.strftime('%Y-%m-%d')] for t in trans]
    return generate_pdf("Financial_Report", "Financial Transaction Summary", ['Transaction ID', 'Amount', 'Date'], data)

# ---------------------------------------------
# CLIENT SIDE VIEWS
# ---------------------------------------------
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
    # Get the disorder type from the URL, default to 'general'
    disorder_type = request.GET.get('type', 'general')

    # Clinical Question Bank
    assessment_data = {
        'general': {
            'title': 'General Mental Health Check-in',
            'theme_color': 'chiromo-navy',
            'questions': [
                {'id': 'q_dep', 'label': 'Little interest or pleasure in doing things? (Mood)'},
                {'id': 'q_anx', 'label': 'Feeling nervous, anxious or on edge? (Anxiety)'},
                {'id': 'q_sub', 'label': 'Have you felt you ought to cut down on your drinking or drug use? (Habits)'},
                {'id': 'q_slp', 'label': 'Trouble falling or staying asleep, or sleeping too much? (Sleep)'},
            ]
        },
        'depression': {
            'title': 'Depression Screening (PHQ-9)',
            'theme_color': 'purple',
            'questions': [
                {'id': 'q1', 'label': 'Little interest or pleasure in doing things'},
                {'id': 'q2', 'label': 'Feeling down, depressed, or hopeless'},
                {'id': 'q3', 'label': 'Trouble falling or staying asleep, or sleeping too much'}
            ]
        },
        'anxiety': {
            'title': 'Anxiety Screening (GAD-7)',
            'theme_color': 'blue',
            'questions': [
                {'id': 'q1', 'label': 'Feeling nervous, anxious or on edge'},
                {'id': 'q2', 'label': 'Not being able to stop or control worrying'},
                {'id': 'q3', 'label': 'Trouble relaxing'}
            ]
        },
        'substance': {
            'title': 'Substance Use Screening (CAGE)',
            'theme_color': 'orange',
            'questions': [
                {'id': 'q1', 'label': 'Have you ever felt you ought to cut down on your drinking or drug use?'},
                {'id': 'q2', 'label': 'Have people annoyed you by criticizing your drinking or drug use?'},
                {'id': 'q3', 'label': 'Have you ever felt bad or guilty about your drinking or drug use?'}
            ]
        },
        'ptsd': {
            'title': 'PTSD Screening (PC-PTSD-5)',
            'theme_color': 'indigo',
            'questions': [
                {'id': 'q1',
                 'label': 'Have you had nightmares about the event or thought about it when you did not want to?'},
                {'id': 'q2',
                 'label': 'Tried hard not to think about the event or went out of your way to avoid situations that reminded you of it?'},
                {'id': 'q3', 'label': 'Were you constantly on guard, watchful, or easily startled?'}
            ]
        }
    }

    # Fallback to general if type doesn't match
    context = assessment_data.get(disorder_type, assessment_data['general'])

    if request.method == 'POST':
        # Here you would calculate the score and redirect to results
        # For now, we'll just simulate a result based on the type
        return render(request, 'appointments/public_result.html', {
            'result_title': f"Analysis for {context['title']}",
            'result_desc': "Your responses suggest a moderate level of symptoms. This screening is not a diagnosis, but an indicator that speaking with a professional could be beneficial.",
            'specialty': 'clinical' if disorder_type in ['depression', 'anxiety', 'ptsd'] else 'addiction'
        })

    return render(request, 'appointments/take_assessment.html', context)
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
        text = request.POST.get("text", "").strip()
        phone_number = request.POST.get("phoneNumber")

        text_parts = text.split('*') if text else []
        level = len(text_parts)
        response = ""

        # LEVEL 0 to 4
        if text == "":
            response = "CON Welcome to CMHS\n1. Book Therapy\n2. Emergency Help\n3. My Account"
        elif level == 1:
            if text_parts[0] == "1":
                response = "CON Select Service:\n1. Depression Support\n2. Anxiety & Stress\n3. Addiction Recovery"
            elif text_parts[0] == "2":
                response = "CON EMERGENCY\nEnter your location:"
            else:
                response = "END Invalid choice."
        elif level == 2:
            response = "CON Select Time:\n1. Today 2:00 PM\n2. Tomorrow 10:00 AM\n3. Monday 9:00 AM"
        elif level == 3:
            response = "CON Select Branch:\n1. Chiromo Lane (Main)\n2. Bustani (Lavington)\n3. Braeside Clinic"
        elif level == 4:
            response = "CON Enter your Full Name to confirm:"

        elif level == 5:
            try:
                service_choice = text_parts[1]
                time_choice = text_parts[2]
                branch_choice = text_parts[3]
                user_name = text_parts[4]

                curr_date = date.today()

                if time_choice == "1":
                    d, t = curr_date, time(14, 0)
                elif time_choice == "2":
                    d, t = curr_date + timedelta(days=1), time(10, 0)
                else:
                    d, t = curr_date + timedelta(days=2), time(9, 0)

                branches = {"1": "Chiromo Lane", "2": "Bustani", "3": "Braeside"}
                selected_branch = branches.get(branch_choice, "Main Branch")

                # Handle User lookup/creation
                patient = User.objects.filter(phone_number=phone_number).first()
                if not patient:
                    patient = User.objects.create(
                        username=phone_number,
                        first_name=user_name,
                        phone_number=phone_number
                    )
                else:
                    patient.first_name = user_name
                    patient.save()

                # Assign Therapist
                therapist = User.objects.filter(is_staff=True).first()

                # --- SAVE THE APPOINTMENT ---
                Appointment.objects.create(
                    patient=patient,
                    therapist=therapist,
                    date=d,
                    time=t,
                    mode='physical',
                    status='pending',
                    notes=f"Branch: {selected_branch}. Service: {service_choice}"
                )

                # --- SEND SMS ---
                sms_text = f"Thank you {user_name}! Your session at {selected_branch} is confirmed for {d} at {t}."
                send_ussd_sms(phone_number, sms_text)

                response = f"END {sms_text}"

            except Exception as e:
                print(f"USSD Final Level Error: {e}")
                response = "END Sorry, an error occurred. Please try again."

        return HttpResponse(response, content_type='text/plain')
def ussd_simulator(request):
    return render(request, 'ussd_simulator.html')


