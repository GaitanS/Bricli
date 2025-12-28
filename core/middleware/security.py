import logging
import json

logger = logging.getLogger("audit")

class AuditLoggingMiddleware:
    """
    Middleware to log sensitive actions (POST requests).
    Inspired by OWASP logging recommendations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.sensitive_keywords = [
            "login", "register", "password", "order", "quote", "profile",
            "autentificare", "inregistrare", "comanda", "oferta", "parola", "profil"
        ]

    def __call__(self, request):
        if request.method == "POST":
            # Check if URL is sensitive
            is_sensitive = any(kw in request.path.lower() for kw in self.sensitive_keywords)

            if is_sensitive:
                user = request.user if request.user.is_authenticated else "Anonymous"
                ip = self.get_client_ip(request)

                # Log the basic action
                logger.info(
                    f"Audit: User={user} IP={ip} Action=POST Path={request.path}"
                )

                # For highly critical paths, you might want to log part of the body
                # (SENSITIVE: Never log passwords or secrets)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
