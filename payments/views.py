from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse

from appointments.models import Appointment, Payment
from .models import Transaction
from .mpesa import lipa_na_mpesa_online
import json
from django.core.mail import send_mail
from .sms_service import send_ussd_sms



@login_required
def pricing_page(request):
    return render(request, 'payments/pricing.html')

@login_required
def payment_success(request):
    return render(request, 'payments/success.html')


@login_required
def initiate_payment(request, appointment_id=None):
    """
    Handles M-Pesa STK Push for clinical sessions.
    Links the transaction to a specific appointment.
    """
    user = request.user

    appointment = None
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        amount = 1
        transaction_desc = f"Therapy Session: {appointment.therapist.last_name}"
    else:

        amount = 1
        transaction_desc = "CMHS Premium Subscription"

    if request.method == 'POST':
        phone = request.POST.get('phone')

        if not phone:
            messages.error(request, "Please enter a phone number.")
            return render(request, 'payments/initiate.html', {'appointment': appointment})


        formatted_phone = '254' + phone[1:] if phone.startswith('0') else phone if phone.startswith('254') else phone


        transaction = Transaction.objects.create(
            user=user,
            phone_number=formatted_phone,
            amount=amount,
            status='pending'
        )

        # 2. Trigger M-Pesa STK Push
        callback_url = "https://cmhs.onrender.com/appointments/mpesa-callback/"
        res = lipa_na_mpesa_online(formatted_phone, amount, callback_url)

        if res.get('ResponseCode') == '0':

            transaction.checkout_request_id = res['CheckoutRequestID']
            transaction.save()


            if appointment:
                Payment.objects.create(
                    patient=user,
                    appointment=appointment,
                    amount=amount,
                    transaction_code=res['CheckoutRequestID'],
                    status='pending'
                )

            messages.success(request, f"STK Push sent to {phone}. Please enter your PIN.")
            return redirect('payment_success')

        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f"M-Pesa Error: {res.get('errorMessage', 'Connection failed')}")
            return redirect('dashboard')

    return render(request, 'payments/initiate.html', {
        'appointment': appointment,
        'amount': amount,
        'phone': user.phone_number
    })

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk = data.get('Body', {}).get('stkCallback', {})

            if stk.get('ResultCode') == 0:
                checkout_id = stk.get('CheckoutRequestID')
                metadata = stk.get('CallbackMetadata', {}).get('Item', [])

                mpesa_code = None
                amount_paid = None
                phone_used = None

                for item in metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_code = item.get('Value')
                    elif item.get('Name') == 'Amount':
                        amount_paid = item.get('Value')
                    elif item.get('Name') == 'PhoneNumber':
                        phone_used = item.get('Value')

                # Update the Transaction Record
                tx = Transaction.objects.get(checkout_request_id=checkout_id)
                tx.status = 'completed'
                tx.transaction_code = mpesa_code
                tx.save()

                # Update User Status
                user = tx.user
                user.is_premium = True
                user.save()

                # Update the Appointment Payment
                try:
                    pay_record = Payment.objects.get(transaction_code=checkout_id)
                    pay_record.status = 'completed'
                    pay_record.transaction_code = mpesa_code
                    pay_record.save()


                    if pay_record.appointment:
                        pay_record.appointment.status = 'confirmed'
                        pay_record.appointment.save()
                except Payment.DoesNotExist:
                    pass

        except Exception as e:
            print(f"Callback Logic Error: {e}")

    return JsonResponse({'status': 'ok'})


@login_required
def generate_receipt(request, tx_id):
    """
    Fetches transaction metadata and renders a printable clinical receipt.
    """
    # Look for the transaction in the Transaction model
    transaction = get_object_or_404(Transaction, id=tx_id)

    context = {
        'full_name': request.user.get_full_name() or request.user.username,
        'transaction_code': transaction.transaction_code,
        'amount': transaction.amount,
        'date': transaction.timestamp,
        'phone': transaction.phone_number,
        'status': transaction.status,
        'hospital': "Chiromo Mental Health Hospital",
        'motto': "Recovery in Dignity"
    }
    return render(request, 'payments/receipt.html', context)

@login_required
def transaction_history(request):
    """
    Renders the financial history for the authenticated patient.
    Aggregates both Premium Subscriptions and Individual Session Payments.
    """
    # 1. Fetch Premium Subscriptions (from the Transaction model)
    # Ordered by newest first
    subscriptions = Transaction.objects.filter(
        user=request.user
    ).order_by('-timestamp')

    # 2. Fetch Individual Session Payments (from the Payment model)
    # This captures payments specifically linked to appointments
    session_payments = Payment.objects.filter(
        patient=request.user
    ).select_related('appointment', 'appointment__therapist').order_by('-timestamp')

    # 3. Context for the template
    context = {
        'subscriptions': subscriptions,
        'session_payments': session_payments,
        'page_title': "My Financial Records"
    }

    return render(request, 'payments/history.html', context)