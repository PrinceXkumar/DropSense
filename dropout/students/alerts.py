"""
Alert service — sends notifications for high-risk students.

Supports:
  • Email  (Django's built-in send_mail)
  • Telegram (HTTP API via requests)
"""

from django.conf import settings
from django.core.mail import send_mail


def send_high_risk_email(student, risk_data, recipients):
    """Send an email alert for a high-risk student."""
    subject = f"⚠️ High Risk Alert: Student #{student.id} — {student.course}"
    reasons_text = "\n".join(f"  • {r}" for r in risk_data["reasons"])
    message = (
        f"Student #{student.id} has been flagged as HIGH RISK.\n\n"
        f"Risk Score : {risk_data['risk_score']}%\n"
        f"Risk Level : {risk_data['risk_level']}\n\n"
        f"Key Reasons:\n{reasons_text}\n\n"
        f"Please review this student's profile and take appropriate action."
    )
    send_mail(
        subject,
        message,
        getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
        recipients,
        fail_silently=False,
    )


def send_telegram_alert(student, risk_data, bot_token=None, chat_id=None):
    """Send a Telegram message for a high-risk student."""
    try:
        import requests
    except ImportError:
        return

    bot_token = bot_token or getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        return

    reasons_text = "\n".join(f"• {r}" for r in risk_data["reasons"])
    text = (
        f"🚨 *High Risk Alert*\n\n"
        f"Student: #{student.id}\n"
        f"Course: {student.course}\n"
        f"Risk Score: {risk_data['risk_score']}%\n"
        f"Level: {risk_data['risk_level']}\n\n"
        f"Reasons:\n{reasons_text}"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(
        url,
        data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )
