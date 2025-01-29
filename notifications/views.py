from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

# Function to handle sending the email
def send_email(address, subject, message):
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error sending email: {e}"}

# API route to handle email sending with hardcoded sample data
def send_email_api(request):
        # Hardcoded sample data
        address = "mkalidozo3@example.com"
        subject = "Sample Subject"
        message = "This is a sample message to test the email functionality."

        # Call the email function and return the response
        response = send_email(address, subject, message)
        return JsonResponse(response, status=200 if response['success'] else 500)

