from django.contrib.auth import get_user_model
from django.db import models
import uuid

from accounts.models import City, County, CraftsmanProfile

User = get_user_model()


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS class pentru icon")
    icon_emoji = models.CharField(max_length=8, default="🔧", help_text="Emoji icon for category")
    description = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)  # Changed to unique for easier lookup
    description = models.TextField(max_length=500, blank=True)
    is_popular = models.BooleanField(default=False, help_text="Popular service shown in suggestions")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class CraftsmanService(models.Model):
    craftsman = models.ForeignKey(CraftsmanProfile, on_delete=models.CASCADE, related_name="services")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    price_from = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_to = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_unit = models.CharField(max_length=50, blank=True, help_text="ex: per oră, per mp, per bucată")

    class Meta:
        unique_together = ["craftsman", "service"]

    def __str__(self):
        return f"{self.craftsman.user.username} - {self.service.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("draft", "Ciornă"),
        ("published", "Publicată"),
        ("awaiting_confirmation", "Așteaptă confirmarea meșterului"),
        ("in_progress", "În progres"),
        ("completed", "Finalizată"),
        ("cancelled", "Anulată"),
    ]

    # Status groups for robust filtering
    COMPLETED_STATUSES = ["completed"]
    CANCELLED_STATUSES = ["cancelled"]
    ACTIVE_STATUSES = ["published", "awaiting_confirmation", "in_progress"]

    URGENCY_CHOICES = [
        ("low", "Nu este urgent"),
        ("medium", "În următoarele săptămâni"),
        ("high", "În următoarele zile"),
        ("urgent", "Urgent"),
    ]

    # Basic info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    # Location
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    address = models.CharField(max_length=300, blank=True)

    # Details
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="medium")
    preferred_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="draft")
    assigned_craftsman = models.ForeignKey(
        CraftsmanProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_orders"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    selected_at = models.DateTimeField(null=True, blank=True, help_text="Când clientul a selectat meșterul")
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="Când meșterul a confirmat preluarea")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.client.username}"


class OrderImage(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="order_images/")
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.title} - Image"


class Quote(models.Model):
    STATUS_CHOICES = [
        ("pending", "În așteptare"),
        ("accepted", "Acceptată"),
        ("rejected", "Respinsă"),
        ("declined", "Refuzată de meșter"),
        ("expired", "Expirată"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="quotes")
    craftsman = models.ForeignKey(CraftsmanProfile, on_delete=models.CASCADE, related_name="quotes")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=1000)

    # Duration fields - structured data
    duration_value = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Valoare durată",
        help_text="Numărul de unități de timp (ex: 5 pentru '5 zile')"
    )
    duration_unit = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('hours', 'Ore'),
            ('days', 'Zile'),
            ('weeks', 'Săptămâni'),
            ('months', 'Luni'),
        ],
        verbose_name="Unitate durată",
        help_text="Unitatea de măsură pentru durată"
    )

    # Keep for backwards compatibility & display
    estimated_duration = models.CharField(max_length=100, blank=True)

    proposed_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data propusă pornire",
        help_text="Data la care meșterul propune să înceapă lucrarea"
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["order", "craftsman"]

    def __str__(self):
        return f"Ofertă pentru {self.order.title} de la {self.craftsman.user.username}"

    def save(self, *args, **kwargs):
        """Auto-generate estimated_duration from duration_value + duration_unit"""
        if self.duration_value and self.duration_unit:
            # Romanian plural forms
            unit_map = {
                'hours': 'oră' if self.duration_value == 1 else 'ore',
                'days': 'zi' if self.duration_value == 1 else 'zile',
                'weeks': 'săptămână' if self.duration_value == 1 else 'săptămâni',
                'months': 'lună' if self.duration_value == 1 else 'luni',
            }
            self.estimated_duration = f"{self.duration_value} {unit_map[self.duration_unit]}"
        super().save(*args, **kwargs)


class QuoteAttachment(models.Model):
    """Atașamente pentru oferte (imagini, PDF-uri, documente)"""

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="quote_attachments/%Y/%m/")

    FILE_TYPE_CHOICES = [
        ("image", "Imagine"),
        ("pdf", "PDF"),
        ("document", "Document"),
        ("other", "Altele"),
    ]
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveIntegerField(help_text="Mărime fișier în bytes")

    description = models.CharField(max_length=200, blank=True, help_text="Descriere scurtă (opțional)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Atașament Ofertă"
        verbose_name_plural = "Atașamente Oferte"

    def __str__(self):
        return f"Atașament {self.file_type} - {self.quote}"

    @property
    def file_size_mb(self):
        """Returnează mărimea fișierului în MB"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def filename(self):
        """Returnează numele fișierului fără path"""
        import os
        return os.path.basename(self.file.name)


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="review")
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="given_reviews")
    craftsman = models.ForeignKey(CraftsmanProfile, on_delete=models.CASCADE, related_name="received_reviews")

    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(max_length=1000, blank=True)

    # Detailed ratings
    quality_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    punctuality_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    communication_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review pentru {self.craftsman.user.username} - {self.rating} stele"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="review_images/")
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review Image - {self.review.craftsman.user.username}"


# Notification helper functions moved to services.logic


# MyBuilder-style Lead System Models


class Invitation(models.Model):
    """Invitații trimise de clienți către meșteri pentru a oferta"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="invitations")
    craftsman = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="sent_invitations")

    STATUS_CHOICES = [
        ("pending", "În așteptare"),
        ("accepted", "Acceptată"),
        ("declined", "Refuzată"),
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("order", "craftsman")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitație pentru {self.craftsman.get_full_name()} - {self.order.title}"


class Shortlist(models.Model):
    """Shortlisting MyBuilder-style - clientul alege meșterii cu care vrea să vorbească"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shortlists")
    craftsman = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="shortlisted_for")

    # Lead fee system
    lead_fee_amount = models.PositiveIntegerField(default=0, help_text="Taxa în bani (cents)")
    charged_at = models.DateTimeField(null=True, blank=True, help_text="Când s-a deductat taxa")
    revealed_contact_at = models.DateTimeField(null=True, blank=True, help_text="Când s-au afișat datele de contact")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("order", "craftsman")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Shortlist: {self.craftsman.get_full_name()} pentru {self.order.title}"

    @property
    def lead_fee_lei(self):
        """Returnează taxa în lei"""
        return self.lead_fee_amount / 100

    @property
    def is_contact_revealed(self):
        """Verifică dacă contactul a fost deblocat - MODIFICAT: contactele sunt întotdeauna vizibile"""
        return True  # Contactele sunt întotdeauna vizibile


# REMOVED: CreditWallet and WalletTransaction models
# Wallet system removed in favor of subscription-based model
# All wallet data exported to CSV before removal (see subscriptions/management/commands/export_wallet_data.py)
# Transition date: 2025-10-18
# Migration: subscriptions/migrations/00XX_remove_wallet_system.py


class CoverageArea(models.Model):
    """Zona de acoperire geografică pentru meșteri"""

    profile = models.OneToOneField("accounts.CraftsmanProfile", on_delete=models.CASCADE, related_name="coverage")
    base_city = models.ForeignKey("accounts.City", on_delete=models.PROTECT, help_text="Orașul de bază")
    radius_km = models.PositiveSmallIntegerField(default=30, help_text="Raza de acoperire în km")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.profile.user.get_full_name()} - {self.base_city.name} ({self.radius_km}km)"

    class Meta:
        verbose_name = "Zonă de acoperire"
        verbose_name_plural = "Zone de acoperire"


# Helper functions for Quote Attachments
def validate_quote_attachment(file):
    """Validează tipul și mărimea fișierului pentru atașamente oferte"""
    import os
    from django.core.exceptions import ValidationError

    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if file.size > max_size:
        raise ValidationError(f"Fișierul este prea mare ({file.size / (1024 * 1024):.1f}MB). Mărimea maximă permisă este 5MB.")

    # Check file extension
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"]
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Tip fișier nepermis ({ext}). Tipuri permise: {', '.join(allowed_extensions)}"
        )

    return file


def detect_file_type(file):
    """Detectează tipul fișierului bazat pe extensie"""
    import os

    ext = os.path.splitext(file.name)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".gif"]:
        return "image"
    elif ext == ".pdf":
        return "pdf"
    elif ext in [".doc", ".docx"]:
        return "document"
    else:
        return "other"
