from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
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
def initiate_payment(request):
    if request.method == 'POST':
        user = request.user
        phone = request.POST.get('phone')

        if not phone:
            messages.error(request, "Please enter a phone number.")
            return redirect('pricing_page')

        # Format for Africa's Talking (+254...)
        if phone.startswith('0'):
            formatted_phone = '+254' + phone[1:]
        elif phone.startswith('254'):
            formatted_phone = '+' + phone
        else:
            formatted_phone = phone

        transaction = Transaction.objects.create(
            user=user,
            phone_number=phone,
            amount=1500,
            status='pending'
        )

        callback_url = "https://google.com"
        response = lipa_na_mpesa_online(phone, 1500, callback_url)

        if response.get('ResponseCode') == '0':
            transaction.checkout_request_id = response['CheckoutRequestID']
            transaction.status = 'completed'
            transaction.save()

            user.is_premium = True
            user.save()

            # 📧 1. SEND EMAIL (SRS REQ-3)
            subject = "Payment Confirmed - Premium Access Unlocked"
            email_message = f"Dear {user.first_name},\n\nYour KES 1,500 payment is confirmed. Transaction: {transaction.checkout_request_id}."
            send_mail(subject, email_message, "notifications@chiromo.co.ke", [user.email])

            # 📱 2. SEND SMS (SRS REQ-5 / SDS Context Diagram)
            sms_text = f"Hello {user.first_name}, your KES 1,500 payment to Chiromo MHS is confirmed. Transaction: {transaction.checkout_request_id}. Recovery in Dignity."
            send_ussd_sms(formatted_phone, sms_text)

            messages.success(request, f"Notification sent to {phone}. Premium unlocked!")
            return redirect('payment_success')

        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f"M-Pesa Error: {response.get('errorMessage')}")
            return redirect('dashboard')

    return redirect('pricing_page')


@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        stk = data.get('Body', {}).get('stkCallback', {})

        if stk.get('ResultCode') == 0:
            checkout_id = stk.get('CheckoutRequestID')
            try:
                tx = Transaction.objects.get(checkout_request_id=checkout_id)
                tx.status = 'completed'
                tx.save()

                # Activate User
                tx.user.is_premium = True
                tx.user.save()
            except Transaction.DoesNotExist:
                pass

    return JsonResponse({'status': 'ok'})