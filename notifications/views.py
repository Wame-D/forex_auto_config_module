from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

# Predefined message templates
MESSAGE_TEMPLATES = {
    "trade_entry": "The bot has entered a trade.",
    "trade_profit": "Congratulations! Your trade has closed in profit. Keep up the great trading discipline.",
    "trade_loss": "Unfortunately, your trade has closed at a loss. Remember to analyze and adjust your strategy.",
    "margin_call": "Warning! Your margin level is low. Please check your account to avoid liquidation.",
    "stop_loss_hit": "Your stop-loss has been triggered, and the trade has been closed. Review your risk management.",
    "take_profit_hit": "Your take-profit level has been reached, and the trade has closed in profit.",
    "news_alert": "Important market news is affecting volatility. Be cautious with open positions.",
    "withdrawal_success": "Your withdrawal request has been processed successfully.",
    "deposit_success": "Your deposit has been received and credited to your account.",
}

# Function to send an email notification
def send_email(address, subject, message_type):
    message = MESSAGE_TEMPLATES.get(message_type, "No message template found for this type.")
    
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error sending email: {e}"}

# API route with hardcoded values
def send_email_api(request):
    # Hardcoded values
    email_address = "mkalidozo3@gmail.com"
    subject = "FXAuto Notification"
    message_type = "trade_entry"  # Change this to send different messages

    response = send_email(email_address, subject, message_type)
    return JsonResponse(response, status=200 if response['success'] else 500)
