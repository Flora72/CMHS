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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00183E")),
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
#   CLIENT SIDE VIEWS
#   APPOINTMENT VIEWS
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
    """
    Handles the booking of clinical sessions.
    Updated to redirect to the M-Pesa payment gateway before final confirmation.
    """
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # 1. Save the appointment but keep it in 'pending' status
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'pending'
            appointment.save()

            # 2. Generate the Telehealth Link (if online)
            if appointment.mode == 'online':
                date_str = appointment.date.strftime('%Y%m%d')
                # Custom Jitsi/8x8 URL structure for Chiromo
                appointment.meeting_link = f"https://8x8.vc/vpaas-magic-cookie-chiromo-demo/CMHS-Therapy-{appointment.id}-{date_str}"
                appointment.save()

            # 3. Trigger Email Notification (Drafting the record)
            subject = 'Appointment Initiated - Chiromo Hospital'
            meeting_info = appointment.meeting_link if appointment.mode == 'online' else 'Physical Session at Branch'

            message = f"""
Dear {request.user.first_name},

Your appointment request has been received. 

Therapist: Dr. {appointment.therapist.last_name}
Date: {appointment.date}
Time: {appointment.time}
Session Type: {appointment.mode}
Status: Pending Payment

Please complete your M-Pesa transaction to finalize this booking.
Meeting Link (Active after payment): {meeting_info}

Recovery in Dignity.
            """

            send_mail(
                subject,
                message,
                'noreply@chiromo.com',
                [request.user.email],
                fail_silently=True
            )
            messages.info(request, 'Appointment saved. Please enter your M-Pesa PIN to finalize the session fee.')
            return redirect('initiate_payment', appointment_id=appointment.id)

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

     # Form Submission
    if request.method == 'POST':
        form = SessionLogForm(request.POST, request.FILES)
        if form.is_valid():
            session_log = form.save(commit=False)


            session_log.appointment = appointment
            session_log.therapist = request.user
            session_log.patient = appointment.patient
            session_log.save()

            # Mark Appointment as Completed
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


    resources = SessionLog.objects.filter(
        patient=request.user
    ).exclude(resources='').order_by('-session_date')

    # Public Resources
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

    return render(request, 'appointments/patient_resources.html', context)

@login_required
def patient_appointments(request):
    # all appointments for the patients are fetched
    appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')

    return render(request, 'appointments/patient_appointments.html', {'appointments': appointments})

@login_required
def log_mood(request, mood_value):
    today = timezone.now().date()
    existing_entry = MoodEntry.objects.filter(patient=request.user, created_at=today).exists()

    if not existing_entry:
        MoodEntry.objects.create(patient=request.user, mood=mood_value)
        messages.success(request, "Mood logged successfully!")
    else:
        messages.info(request, "You have already logged your mood for today.")

    return redirect('dashboard')

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

# ---------------------------------------------
# MESSAGES VIEWS
# ---------------------------------------------
@login_required
@premium_required
def inbox(request, id=None):
    user = request.user
    chat_partner = None
    if id:
        chat_partner = get_object_or_404(User, id=id)

    # RECENT CONTACTS
    sent_ids = Message.objects.filter(sender=user).values_list('recipient', flat=True)
    received_ids = Message.objects.filter(recipient=user).values_list('sender', flat=True)
    contact_ids = set(list(sent_ids) + list(received_ids))
    recent_contacts = User.objects.filter(id__in=contact_ids).exclude(id=user.id)


    # Using 'therapist_appointments' and 'patient_appointments'
    if user.role == 'therapist':
        # Therapist sees patients who have booked with them
        my_contacts = User.objects.filter(
            patient_appointments__therapist=user
        ).distinct()
    else:
        # Patient sees therapists they have booked with
        my_contacts = User.objects.filter(
            therapist_appointments__patient=user
        ).distinct()

    return render(request, 'appointments/inbox.html', {
        'chat_partner': chat_partner,
        'recent_contacts': recent_contacts,
        'my_contacts': my_contacts,
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
        is_owner = (msg.sender == request.user)
        is_deleted = (msg.body == "This message was deleted")

        data.append({
            'id': msg.id,
            'sender': 'me' if is_owner else 'partner',
            'body': msg.body,
            'timestamp': timezone.localtime(msg.timestamp).strftime("%H:%M"),
            'can_edit': is_owner and not is_deleted,
            'can_delete': is_owner and not is_deleted,
            'is_deleted': is_deleted
        })

    return JsonResponse({'messages': data})

@login_required
def delete_message(request, msg_id):
    # Verify ownership
    message = get_object_or_404(Message, id=msg_id, sender=request.user)

    # Delete
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


# ---------------------------------------------
# GENERAL ASSESSMENT VIEWS
# ---------------------------------------------
def assessment_hub(request):
    return render(request, 'appointments/assessment_hub.html')

def take_assessment(request):
    disorder_type = request.GET.get('type', 'general')

    # Define the questions and scoring thresholds for each test
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
                {'id': 'q3', 'label': 'Trouble falling or staying asleep, or sleeping too much'},
                {'id': 'q4', 'label': 'Feeling tired or having little energy'},
                {'id': 'q5', 'label': 'Poor appetite or overeating'}
            ]
        },
        'anxiety': {
            'title': 'Anxiety Screening (GAD-7)',
            'theme_color': 'blue',
            'questions': [
                {'id': 'q1', 'label': 'Feeling nervous, anxious or on edge'},
                {'id': 'q2', 'label': 'Not being able to stop or control worrying'},
                {'id': 'q3', 'label': 'Worrying too much about different things'},
                {'id': 'q4', 'label': 'Trouble relaxing'},
                {'id': 'q5', 'label': 'Being so restless that it is hard to sit still'}
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
                {'id': 'q1', 'label': 'Have you had nightmares about the event or thought about it when you did not want to?'},
                {'id': 'q2', 'label': 'Tried hard not to think about the event or went out of your way to avoid situations that reminded you of it?'},
                {'id': 'q3', 'label': 'Were you constantly on guard, watchful, or easily startled?'}
            ]
        },
        'bipolar': {
            'title': 'Bipolar Screening',
            'theme_color': 'pink',
            'questions': [
                {'id': 'q1', 'label': 'Has there ever been a period where you felt so good/hyper that you got into trouble?'},
                {'id': 'q2', 'label': 'During this time, did you need less sleep than usual?'},
                {'id': 'q3', 'label': 'Were you more talkative or did you speak faster than usual?'},
                {'id': 'q4', 'label': 'Did you spend money purely on impulse?'},
                {'id': 'q5', 'label': 'Did you experience racing thoughts?'}
            ]
        }
    }

    context = assessment_data.get(disorder_type, assessment_data['general'])

    if request.method == 'POST':
        # Collect all numerical values from the radio buttons
        total_score = 0
        for q in context['questions']:
            value = request.POST.get(q['id'], 0)
            total_score += int(value)

        # 2. Dynamic Logic Gate
        if total_score >= 12:
            severity = "Severe Symptoms"
            desc = "Your responses suggest a high level of symptoms. We strongly recommend scheduling a comprehensive clinical evaluation with a psychiatrist."
        elif total_score >= 6:
            severity = "Moderate Symptoms"
            desc = "Your responses suggest moderate symptoms. Speaking with a therapist or counselor would be a helpful next step."
        else:
            severity = "Minimal Symptoms"
            desc = "Your responses suggest minimal symptoms at this time. Continue prioritizing your wellness and check back if anything changes."

        return render(request, 'appointments/public_result.html', {
            'result_title': f"Analysis: {severity}",
            'result_desc': desc,
            'score': total_score,
            'specialty': 'clinical' if disorder_type in ['depression', 'anxiety', 'ptsd', 'bipolar'] else 'addiction'
        })

    return render(request, 'appointments/take_assessment.html', context)

# ---------------------------------------------
# JOURNAL RELATED VIEWS
# ---------------------------------------------
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

@login_required
def delete_journal(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, patient=request.user)
    entry.delete()
    messages.success(request, "Entry deleted.")
    return redirect('journal')

@login_required
def edit_journal(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, patient=request.user)
    if request.method == 'POST':
        entry.title = request.POST.get('title')
        entry.content = request.POST.get('content')
        entry.mood_rating = request.POST.get('mood')
        entry.save()
        return redirect('journal')
    return render(request, 'appointments/edit_journal.html', {'entry': entry})


# ---------------------------------------------
# USSD RELATED VIEWS
# ---------------------------------------------
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

                # SEND SMS
                sms_text = f"Thank you {user_name}! Your session at {selected_branch} is confirmed for {d} at {t}."
                send_ussd_sms(phone_number, sms_text)

                response = f"END {sms_text}"

            except Exception as e:
                print(f"USSD Final Level Error: {e}")
                response = "END Sorry, an error occurred. Please try again."

        return HttpResponse(response, content_type='text/plain')
def ussd_simulator(request):
    return render(request, 'ussd_simulator.html')


