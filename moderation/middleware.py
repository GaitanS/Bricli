"""
Middleware for moderation and anti-abuse
"""

import time

from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

from .models import block_ip, is_ip_blocked


class IPBlockingMiddleware(MiddlewareMixin):
    """
    Middleware pentru blocarea IP-urilor
    """

    def process_request(self, request):
        # Obține IP-ul real al utilizatorului
        ip_address = self.get_client_ip(request)

        # Verifică dacă IP-ul este blocat
        if is_ip_blocked(ip_address):
            return HttpResponseForbidden(
                render(request, "moderation/ip_blocked.html", {"ip_address": ip_address}).content
            )

        # Salvează IP-ul în request pentru utilizare ulterioară
        request.client_ip = ip_address
        return None

    def get_client_ip(self, request):
        """
        Obține IP-ul real al clientului, ținând cont de proxy-uri
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class RateLimitingMiddleware(MiddlewareMixin):
    """
    Middleware pentru rate limiting global
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}  # IP -> (count, timestamp)
        self.max_requests_per_minute = 60
        super().__init__(get_response)

    def process_request(self, request):
        if not hasattr(request, "client_ip"):
            return None

        ip_address = request.client_ip
        current_time = time.time()

        # Curăță intrările vechi (mai vechi de 1 minut)
        self.cleanup_old_entries(current_time)

        # Verifică rate limiting pentru IP
        if ip_address in self.request_counts:
            count, first_request_time = self.request_counts[ip_address]

            # Dacă sunt în aceeași fereastră de timp (1 minut)
            if current_time - first_request_time < 60:
                if count >= self.max_requests_per_minute:
                    # Blochează IP-ul temporar pentru flood
                    block_ip(
                        ip_address=ip_address,
                        reason="flood",
                        duration_hours=1,
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    )

                    return HttpResponseForbidden(
                        render(request, "moderation/rate_limited.html", {"ip_address": ip_address}).content
                    )
                else:
                    # Incrementează contorul
                    self.request_counts[ip_address] = (count + 1, first_request_time)
            else:
                # Nouă fereastră de timp
                self.request_counts[ip_address] = (1, current_time)
        else:
            # Prima cerere pentru acest IP
            self.request_counts[ip_address] = (1, current_time)

        return None

    def cleanup_old_entries(self, current_time):
        """
        Curăță intrările mai vechi de 1 minut
        """
        expired_ips = []
        for ip, (count, timestamp) in self.request_counts.items():
            if current_time - timestamp > 60:
                expired_ips.append(ip)

        for ip in expired_ips:
            del self.request_counts[ip]


class SuspiciousActivityMiddleware(MiddlewareMixin):
    """
    Middleware pentru detectarea activității suspecte
    """

    def process_request(self, request):
        if not hasattr(request, "client_ip"):
            return None

        # Verifică pentru activitate suspectă
        if self.is_suspicious_request(request):
            # Log activitatea suspectă
            self.log_suspicious_activity(request)

            # Opțional: blochează IP-ul
            if self.should_block_ip(request):
                block_ip(
                    ip_address=request.client_ip,
                    reason="suspicious",
                    duration_hours=24,
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )

        return None

    def is_suspicious_request(self, request):
        """
        Detectează cereri suspecte
        """
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

        # Lista de user agents suspecți
        suspicious_agents = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
            "python-requests",
            "scrapy",
            "selenium",
        ]

        # Verifică dacă user agent-ul conține cuvinte suspecte
        for agent in suspicious_agents:
            if agent in user_agent:
                return True

        # Verifică pentru cereri fără user agent
        if not user_agent:
            return True

        # Verifică pentru cereri cu multe parametri (posibil SQL injection)
        if len(request.GET) > 10:
            return True

        return False

    def should_block_ip(self, request):
        """
        Decide dacă să blocheze IP-ul
        """
        # Pentru moment, nu blochează automat
        # Poate fi extins cu logică mai complexă
        return False

    def log_suspicious_activity(self, request):
        """
        Înregistrează activitatea suspectă
        """
        # TODO: Implementează logging în baza de date sau fișier
        pass
