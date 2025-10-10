"""
Core API Views

Health check and monitoring endpoints.
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    """
    Simple health check endpoint for monitoring.

    Returns:
        200 OK: {
            "status": "ok",
            "timestamp": "2025-01-10T14:30:00Z",
            "service": "bricli",
            "version": "1.0.0"
        }

    Usage:
        GET /api/health
        - No authentication required
        - Use for uptime monitoring, load balancer health checks
    """

    permission_classes = [AllowAny]  # Public endpoint

    def get(self, request, *args, **kwargs):
        """Health check GET handler"""
        return Response(
            {
                "status": "ok",
                "timestamp": timezone.now().isoformat(),
                "service": "bricli",
                "version": "1.0.0",
                "environment": "development" if settings.DEBUG else "production",
            },
            status=status.HTTP_200_OK,
        )


# Import settings after class definition to avoid circular import
from django.conf import settings
