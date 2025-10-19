from django.apps import AppConfig


class ServicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "services"

    def ready(self):
        """Import signals when app is ready"""
        import services.signals  # noqa: F401
