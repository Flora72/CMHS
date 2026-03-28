from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
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
    checkout_id = request.GET.get('checkout_id')
    transaction = None

    if checkout_id:
        # Fetch the transaction object updated by the mpesa_callback
        transaction = Transaction.objects.filter(checkout_request_id=checkout_id).first()

    context = {
        'transaction': transaction,
        'full_name': request.user.get_full_name() or request.user.username,
        'is_confirmed': transaction and transaction.transaction_code and not transaction.transaction_code.startswith(
            'ws_')
    }
    return render(request, 'payments/success.html', context)

@login_required
def initiate_payment(request, appointment_id=None):
    """
    Handles M-Pesa STK Push.
    Redirects to success page with checkout_id for real-time data fetching.
    """
    user = request.user
    appointment = None

    # Check if paying for a session or premium
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        amount = 1
    else:
        amount = 1

    if request.method == 'POST':
        phone = request.POST.get('phone')
        if not phone:
            messages.error(request, "Please enter a phone number.")
            return render(request, 'payments/initiate.html', {'appointment': appointment})

        # Format phone for Safaricom
        formatted_phone = '254' + phone[1:] if phone.startswith('0') else phone

        # Create the initial pending transaction
        transaction = Transaction.objects.create(
            user=user,
            phone_number=formatted_phone,
            amount=amount,
            payment_type='session' if appointment_id else 'premium',
            status='pending'
        )

        callback_url = "https://cmhs.onrender.com/payments/callback/"
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

            messages.success(request, "STK Push sent. Please check your handset.")

            base_url = reverse('payment_success')
            return redirect(f"{base_url}?checkout_id={transaction.checkout_request_id}")

        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f"M-Pesa Error: {res.get('errorMessage')}")
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

