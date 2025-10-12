from django.contrib.auth import get_user_model
from django.db import models

from accounts.models import City, County, CraftsmanProfile
from notifications.services import NotificationService

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

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="quotes")
    craftsman = models.ForeignKey(CraftsmanProfile, on_delete=models.CASCADE, related_name="quotes")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=1000)
    estimated_duration = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["order", "craftsman"]

    def __str__(self):
        return f"Ofertă pentru {self.order.title} de la {self.craftsman.user.username}"


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="review")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_reviews")
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


# Notification helper functions
def notify_new_quote(quote):
    """Notify client about new quote using centralized NotificationService"""
    return NotificationService().create_notification(
        recipient=quote.order.client,
        title=f'Ofertă nouă pentru "{quote.order.title}"',
        message=(
            f"{quote.craftsman.user.get_full_name() or quote.craftsman.user.username} "
            f"a trimis o ofertă de {quote.price} RON."
        ),
        notification_type="new_quote",
        priority="high",
        sender=quote.craftsman.user,
        action_url=f"/services/order/{quote.order.id}/",
        related_object_type="quote",
        related_object_id=quote.id,
        data={"order_id": quote.order.id, "quote_id": quote.id, "price": float(quote.price)},
    )


def notify_quote_accepted(quote):
    """Notify craftsman about accepted quote using centralized NotificationService"""
    return NotificationService().create_notification(
        recipient=quote.craftsman.user,
        title="Oferta ta a fost acceptată!",
        message=(
            f'Clientul a acceptat oferta ta pentru "{quote.order.title}". '
            "Te rugăm să confirmi că poți prelua această comandă."
        ),
        notification_type="quote_accepted",
        priority="high",
        action_url=f"/services/order/{quote.order.id}/",
        related_object_type="quote",
        related_object_id=quote.id,
        data={"order_id": quote.order.id, "quote_id": quote.id},
    )


def notify_quote_rejected(quote):
    """Notify craftsman about rejected quote using centralized NotificationService"""
    return NotificationService().create_notification(
        recipient=quote.craftsman.user,
        title="Oferta ta a fost respinsă",
        message=(f'Din păcate, oferta ta pentru "{quote.order.title}" nu a fost acceptată.'),
        notification_type="quote_rejected",
        priority="medium",
        action_url=f"/services/order/{quote.order.id}/",
        related_object_type="quote",
        related_object_id=quote.id,
        data={"order_id": quote.order.id, "quote_id": quote.id},
    )


def notify_order_request(order, craftsman):
    """Notify craftsman about new order request (direct invitation) using NotificationService"""
    return NotificationService().create_notification(
        recipient=craftsman.user,
        notification_type="new_order",
        title="Solicitare nouă de ofertă",
        message=(
            f'Ai primit o solicitare de ofertă pentru "{order.title}" în '
            f"{order.city.name}, {order.county.name}. Clientul așteaptă oferta ta!"
        ),
        priority="high",
        sender=order.client,
        action_url=f"/services/order/{order.id}/",
        related_object_type="order",
        related_object_id=order.id,
        data={"order_id": order.id, "invited_craftsman_id": craftsman.user.id},
    )


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


class CreditWallet(models.Model):
    """Wallet cu credit pentru meșteri - pentru plata lead fees"""

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="wallet")
    balance_cents = models.IntegerField(default=0, help_text="Soldul în bani (cents)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet {self.user.get_full_name()} - {self.balance_lei} lei"

    @property
    def balance_lei(self):
        """Returnează soldul în lei"""
        return self.balance_cents / 100

    def has_sufficient_balance(self, amount_cents):
        """Verifică dacă are suficient credit"""
        return self.balance_cents >= amount_cents

    def deduct_amount(self, amount_cents, reason, meta=None):
        """Deduce o sumă din wallet și creează tranzacția"""
        if not self.has_sufficient_balance(amount_cents):
            raise ValueError("Sold insuficient în wallet")

        self.balance_cents -= amount_cents
        self.save(update_fields=["balance_cents", "updated_at"])

        return WalletTransaction.objects.create(wallet=self, amount_cents=-amount_cents, reason=reason, meta=meta or {})

    def add_amount(self, amount_cents, reason, meta=None):
        """Adaugă o sumă în wallet și creează tranzacția"""
        self.balance_cents += amount_cents
        self.save(update_fields=["balance_cents", "updated_at"])

        return WalletTransaction.objects.create(wallet=self, amount_cents=amount_cents, reason=reason, meta=meta or {})


class WalletTransaction(models.Model):
    """Istoric tranzacții wallet"""

    wallet = models.ForeignKey(CreditWallet, on_delete=models.CASCADE, related_name="transactions")
    amount_cents = models.IntegerField(
        help_text="Suma în bani (cents) - pozitivă pentru încărcare, negativă pentru taxe"
    )

    REASON_CHOICES = [
        ("top_up", "Încărcare credit"),
        ("lead_fee", "Taxă lead (shortlist)"),
        ("refund", "Rambursare"),
        ("bonus", "Bonus"),
        ("adjustment", "Ajustare"),
    ]
    reason = models.CharField(max_length=64, choices=REASON_CHOICES)
    meta = models.JSONField(default=dict, blank=True, help_text="Date suplimentare (order_id, client_id, etc.)")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.amount_cents > 0 else ""
        return f"{sign}{self.amount_lei} lei - {self.get_reason_display()}"

    @property
    def amount_lei(self):
        """Returnează suma în lei"""
        return self.amount_cents / 100


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
