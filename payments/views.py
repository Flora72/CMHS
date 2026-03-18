from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
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


        formatted_phone = '+254' + phone[1:] if phone.startswith('0') else '+' + phone if phone.startswith(
            '254') else phone


        transaction = Transaction.objects.create(
            user=user,
            phone_number=formatted_phone,
            amount=1500,
            status='pending'
        )


        callback_url = "https://cmhs-app.onrender.com/appointments/mpesa_callback/"
        res = lipa_na_mpesa_online(formatted_phone, 1500, callback_url)

        if res.get('ResponseCode') == '0':
            transaction.checkout_request_id = res['CheckoutRequestID']
            transaction.status = 'completed'
            transaction.save()

            user.is_premium = True
            user.save()


            subject = "Payment Confirmed - CMHS Premium Access"
            email_message = (
                f"Dear {user.first_name},\n\n"
                f"Your payment of KES 1,500 for the Online Chiromo Mental Health System is confirmed.\n"
                f"Transaction ID: {transaction.checkout_request_id}\n\n"
                f"Your Premium features are now unlocked. Recovery in Dignity."
            )
            send_mail(subject, email_message, "perpymari@gmail.com", [user.email])


            sms_text = f"Hello {user.first_name}, your KES 1,500 payment to CMHS is confirmed. Transaction: {transaction.checkout_request_id}."
            send_ussd_sms(formatted_phone, sms_text)

            messages.success(request, f"Notification sent to {phone}. Premium unlocked!")
            return redirect('payment_success')

        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, f"M-Pesa Error: {res.get('errorMessage')}")
            return redirect('dashboard')

    return redirect('pricing_page')

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk = data.get('Body', {}).get('stkCallback', {})
            if stk.get('ResultCode') == 0:
                tx = Transaction.objects.get(checkout_request_id=stk.get('CheckoutRequestID'))
                tx.status = 'completed'
                tx.save()
                user = tx.user
                user.is_premium = True
                user.save()
        except Exception as e:
            print(f"Callback Error: {e}")
    return JsonResponse({'status': 'ok'})