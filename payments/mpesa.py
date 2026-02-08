import requests
import json
import base64
from datetime import datetime
from django.conf import settings


def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        r = requests.get(api_url, auth=(consumer_key, consumer_secret))
        r.raise_for_status()
        token = r.json()['access_token']
        return token
    except Exception as e:
        print(f"M-Pesa Auth Error: {e}")
        return None


def lipa_na_mpesa_online(phone_number, amount, callback_url):
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to authenticate with M-Pesa"}

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    data_to_encode = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')

    # Format Phone Number
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+'):
        phone_number = phone_number[1:]

    # Construct Request
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": "CMHS Health",
        "TransactionDesc": "Premium Subscription"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}