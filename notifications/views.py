from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

# Predefined message templates with placeholders for dynamic values
MESSAGE_TEMPLATES = {
    "trade_entry": "Your bot has entered a trade on {date_time}. Stay alert and manage your risk accordingly.",
    "trade_profit": "Congratulations! Your trade closed in profit on {date_time}. Keep up the great trading discipline.",
    "trade_loss": "Unfortunately, your trade closed at a loss on {date_time}. Remember to analyze and adjust your strategy.",
    "margin_call": "Warning! Your margin level is low as of {date_time}. Please check your account to avoid liquidation.",
    "stop_loss_hit": "Your stop-loss was triggered on {date_time}, and the trade has been closed. Review your risk management.",
    "take_profit_hit": "Your take-profit level was reached on {date_time}, and the trade closed in profit.",
    "news_alert": "Important market news is affecting volatility as of {date_time}. Be cautious with open positions.",
    "withdrawal_success": "Your withdrawal request was processed successfully on {date_time}.",
    "deposit_success": "Your deposit was received and credited to your account on {date_time}.",
}

# Function to send an email notification
def send_email(address, subject, message_type, date_time):
    message_template = MESSAGE_TEMPLATES.get(message_type, "No message template found for this type.")
    message = message_template.format(date_time=date_time)

    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error sending email: {e}"}

# API route with hardcoded values and dynamic trade time
def send_email_api(request):
    # Hardcoded values
    email_address = "mkalidozo3@gmail.com"
    subject = "Trading Notification"
    message_type = "trade_entry"  # Change this to send different messages
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current date and time

    response = send_email(email_address, subject, message_type, date_time)
    return JsonResponse(response, status=200 if response['success'] else 500)
