"""
Email configuration for Bricli platform
This file contains email settings for both development and production environments.
"""

import os

from django.conf import settings


# Email backend configuration
def get_email_backend():
    """
    Returns the appropriate email backend based on environment
    """
    if settings.DEBUG:
        return "django.core.mail.backends.console.EmailBackend"
    else:
        return "django.core.mail.backends.smtp.EmailBackend"


# SMTP Configuration for production
PRODUCTION_EMAIL_CONFIG = {
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": os.environ.get("EMAIL_HOST", "smtp.gmail.com"),
    "EMAIL_PORT": int(os.environ.get("EMAIL_PORT", "587")),
    "EMAIL_USE_TLS": os.environ.get("EMAIL_USE_TLS", "True").lower() == "true",
    "EMAIL_USE_SSL": os.environ.get("EMAIL_USE_SSL", "False").lower() == "true",
    "EMAIL_HOST_USER": os.environ.get("EMAIL_HOST_USER", ""),
    "EMAIL_HOST_PASSWORD": os.environ.get("EMAIL_HOST_PASSWORD", ""),
    "EMAIL_TIMEOUT": int(os.environ.get("EMAIL_TIMEOUT", "30")),
}

# Email addresses
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Bricli <noreply@bricli.ro>")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", "server@bricli.ro")
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support@bricli.ro")

# Email subject prefix
EMAIL_SUBJECT_PREFIX = "[Bricli] "

# Email templates mapping
EMAIL_TEMPLATES = {
    "welcome": "emails/welcome_email.html",
    "password_reset": "accounts/password_reset_email.html",
    "order_notification": "emails/order_notification.html",
    "quote_notification": "emails/order_notification.html",
    "project_update": "emails/order_notification.html",
}


# Email sending functions
def send_welcome_email(user):
    """
    Send welcome email to new users
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    subject = f"Bun venit la Bricli, {user.get_full_name() or user.username}!"
    html_message = render_to_string(EMAIL_TEMPLATES["welcome"], {"user": user})
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_order_notification(order, notification_type, recipient):
    """
    Send order-related notifications
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    subject_map = {
        "new_order": "Comandă nouă disponibilă pe Bricli",
        "quote_received": "Ai primit o ofertă nouă",
        "order_accepted": "Felicitări! Oferta ta a fost acceptată",
        "project_update": "Actualizare proiect",
    }

    subject = subject_map.get(notification_type, "Notificare Bricli")

    context = {
        "order": order,
        "notification_type": notification_type,
        "user": recipient,
    }

    # Add specific context based on notification type
    if notification_type == "new_order":
        context["craftsman"] = recipient
    elif notification_type == "quote_received":
        context["client"] = recipient
        # Add quote and craftsman info if available
    elif notification_type == "order_accepted":
        context["craftsman"] = recipient
        # Add client info if available

    html_message = render_to_string(EMAIL_TEMPLATES["order_notification"], context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[recipient.email],
        html_message=html_message,
        fail_silently=False,
    )


# Email validation
def validate_email_settings():
    """
    Validate email configuration
    """
    errors = []

    if not settings.DEBUG:
        required_settings = [
            "EMAIL_HOST_USER",
            "EMAIL_HOST_PASSWORD",
        ]

        for setting in required_settings:
            if not os.environ.get(setting):
                errors.append(f"Missing required email setting: {setting}")

    return errors


# Environment variables template for production
ENVIRONMENT_TEMPLATE = """
# Email Configuration for Bricli Production
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_TIMEOUT=30
DEFAULT_FROM_EMAIL=Bricli <noreply@bricli.ro>
SERVER_EMAIL=server@bricli.ro
SUPPORT_EMAIL=support@bricli.ro
"""
