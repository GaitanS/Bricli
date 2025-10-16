"""
Context processors for Romanian localization and cultural adaptations
"""

from .models import SiteSettings


def romanian_context(request):
    """Add Romanian-specific context variables"""
    return {
        "CURRENCY_SYMBOL": "RON",
        "CURRENCY_NAME": "Lei",
        "COUNTRY_CODE": "RO",
        "COUNTRY_NAME": "România",
        "PHONE_PREFIX": "+40",
        "VAT_RATE": 19,  # Romanian VAT rate
        "BUSINESS_HOURS": {"weekdays": "09:00 - 18:00", "saturday": "09:00 - 14:00", "sunday": "Închis"},
        "POPULAR_CITIES": [
            "București",
            "Cluj-Napoca",
            "Timișoara",
            "Iași",
            "Constanța",
            "Craiova",
            "Brașov",
            "Galați",
            "Ploiești",
            "Oradea",
        ],
        "ROMANIAN_HOLIDAYS": [
            {"name": "Anul Nou", "date": "1-2 ianuarie"},
            {"name": "Boboteaza", "date": "6 ianuarie"},
            {"name": "Paștele", "date": "Variabil"},
            {"name": "Ziua Muncii", "date": "1 mai"},
            {"name": "Ziua Copilului", "date": "1 iunie"},
            {"name": "Adormirea Maicii Domnului", "date": "15 august"},
            {"name": "Sfântul Andrei", "date": "30 noiembrie"},
            {"name": "Ziua Națională", "date": "1 decembrie"},
            {"name": "Crăciunul", "date": "25-26 decembrie"},
        ],
    }


def site_settings_context(request):
    """Add site settings to context"""
    try:
        site_settings = SiteSettings.objects.first()
    except SiteSettings.DoesNotExist:
        site_settings = None

    return {
        "site_settings": site_settings,
        "SITE_NAME": "Bricli",
        "SITE_TAGLINE": "Găsește meșterul potrivit pentru tine",
        "SITE_DESCRIPTION": "Bricli conectează clienții cu meșteri verificați din România. Rapid, sigur și la prețuri corecte.",
        "CONTACT_EMAIL": "contact@bricli.ro",
        "CONTACT_PHONE": "+40 21 123 4567",
        "SOCIAL_MEDIA": {
            "facebook": "https://facebook.com/bricli.ro",
            "instagram": "https://instagram.com/bricli.ro",
            "linkedin": "https://linkedin.com/company/bricli",
        },
    }


def user_context(request):
    """Add user-specific context"""
    context = {}

    if request.user.is_authenticated:
        context["user_type"] = request.user.user_type
        context["is_craftsman"] = request.user.user_type == "craftsman"
        context["is_client"] = request.user.user_type == "client"

        # Get avatar URL (craftsman profile_photo or user profile_picture)
        avatar_url = ""
        if hasattr(request.user, "craftsman_profile"):
            craftsman = request.user.craftsman_profile
            context["craftsman_profile"] = craftsman
            context["has_portfolio"] = craftsman.portfolio_images.exists()
            context["portfolio_count"] = craftsman.portfolio_images.count()

            # Try to get profile photo from craftsman profile
            if craftsman.profile_photo:
                try:
                    avatar_url = craftsman.profile_photo.url
                except Exception:
                    pass

        # Fallback to user profile_picture if no craftsman photo
        if not avatar_url and hasattr(request.user, "profile_picture") and request.user.profile_picture:
            try:
                avatar_url = request.user.profile_picture.url
            except Exception:
                pass

        context["avatar_url"] = avatar_url

        # Get unread notifications count
        try:
            from notifications.models import Notification
            context["unread_notifications_count"] = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
        except Exception:
            context["unread_notifications_count"] = 0

    return context


def navigation_context(request):
    """Add navigation-specific context"""
    return {
        "current_path": request.path,
        "current_url_name": request.resolver_match.url_name if request.resolver_match else None,
        "current_namespace": request.resolver_match.namespace if request.resolver_match else None,
    }
