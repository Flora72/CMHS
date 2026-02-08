import africastalking

username = "sandbox"
api_key = "atsk_daf0dc04d7cfd8767a49ce04e4c01317fc1bcb86481f91e8eca58b1b93f7a9813dbb2a57"

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_ussd_sms(recipient, message):

    try:

        response = sms.send(message, [recipient])
        print(f"SMS Sent Successfully: {response}")
    except Exception as e:
        print(f"SMS failure: {e}")

