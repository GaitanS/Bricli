"""
Models for moderation and anti-abuse system
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from datetime import timedelta

User = get_user_model()


class RateLimit(models.Model):
    """
    Rate limiting pentru acțiuni utilizatori
    """
    LIMIT_TYPES = [
        ('order_creation', 'Creare comenzi'),
        ('quote_creation', 'Creare oferte'),
        ('message_sending', 'Trimitere mesaje'),
        ('profile_updates', 'Actualizări profil'),
        ('review_creation', 'Creare recenzii'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rate_limits')
    limit_type = models.CharField(max_length=50, choices=LIMIT_TYPES)
    count = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField(auto_now_add=True)
    
    # Limite per tip de utilizator
    max_limit_new_user = models.PositiveIntegerField(default=3)  # Utilizatori noi
    max_limit_verified_user = models.PositiveIntegerField(default=10)  # Utilizatori verificați
    window_hours = models.PositiveIntegerField(default=24)  # Fereastra de timp în ore
    
    class Meta:
        unique_together = ['user', 'limit_type']
        verbose_name = "Limită de utilizare"
        verbose_name_plural = "Limite de utilizare"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_limit_type_display()}: {self.count}"
    
    def is_within_window(self):
        """Verifică dacă suntem încă în fereastra de timp"""
        return timezone.now() - self.window_start < timedelta(hours=self.window_hours)
    
    def get_max_limit(self):
        """Returnează limita maximă pentru utilizator"""
        # Utilizatori noi (< 30 zile) au limite mai mici
        if self.user.date_joined > timezone.now() - timedelta(days=30):
            return self.max_limit_new_user
        return self.max_limit_verified_user
    
    def can_perform_action(self):
        """Verifică dacă utilizatorul poate efectua acțiunea"""
        if not self.is_within_window():
            # Resetează contorul dacă fereastra a expirat
            self.count = 0
            self.window_start = timezone.now()
            self.save()
        
        return self.count < self.get_max_limit()
    
    def increment_count(self):
        """Incrementează contorul de acțiuni"""
        if not self.is_within_window():
            self.count = 1
            self.window_start = timezone.now()
        else:
            self.count += 1
        self.save()


class IPBlock(models.Model):
    """
    Blocarea IP-urilor pentru flood/spam
    """
    BLOCK_REASONS = [
        ('flood', 'Flood/Spam'),
        ('abuse', 'Abuz'),
        ('suspicious', 'Activitate suspectă'),
        ('manual', 'Blocare manuală'),
    ]
    
    ip_address = models.GenericIPAddressField()
    reason = models.CharField(max_length=20, choices=BLOCK_REASONS)
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    is_permanent = models.BooleanField(default=False)
    
    # Detalii despre blocare
    user_agent = models.TextField(blank=True)
    blocked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='blocked_ips'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "IP blocat"
        verbose_name_plural = "IP-uri blocate"
        ordering = ['-blocked_at']
    
    def __str__(self):
        return f"IP {self.ip_address} - {self.get_reason_display()}"
    
    def is_active(self):
        """Verifică dacă blocarea este încă activă"""
        if self.is_permanent:
            return True
        if self.blocked_until:
            return timezone.now() < self.blocked_until
        return True


class Report(models.Model):
    """
    Raportări de conținut/utilizatori
    """
    REPORT_TYPES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Conținut nepotrivit'),
        ('fake_profile', 'Profil fals'),
        ('scam', 'Înșelătorie'),
        ('harassment', 'Hărțuire'),
        ('copyright', 'Încălcare drepturi de autor'),
        ('other', 'Altele'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('reviewing', 'În curs de analiză'),
        ('resolved', 'Rezolvat'),
        ('dismissed', 'Respins'),
    ]
    
    # Cine raportează
    reporter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reports_made'
    )
    
    # Ce se raportează (generic pentru orice model)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalii raport
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderare
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='reports_reviewed'
    )
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Raportare"
        verbose_name_plural = "Raportări"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Raport {self.get_report_type_display()} de la {self.reporter.username}"


class ModerationAction(models.Model):
    """
    Acțiuni de moderare efectuate
    """
    ACTION_TYPES = [
        ('warning', 'Avertisment'),
        ('content_removal', 'Ștergere conținut'),
        ('account_suspension', 'Suspendare cont'),
        ('account_ban', 'Interzicere cont'),
        ('profile_restriction', 'Restricție profil'),
    ]
    
    # Cine efectuează acțiunea
    moderator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='moderation_actions'
    )
    
    # Asupra cui se efectuează
    target_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='moderation_actions_received'
    )
    
    # Ce conținut (opțional)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalii acțiune
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    reason = models.TextField()
    duration_hours = models.PositiveIntegerField(null=True, blank=True)  # Pentru suspendări temporare
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Acțiune de moderare"
        verbose_name_plural = "Acțiuni de moderare"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} pentru {self.target_user.username}"
    
    def is_expired(self):
        """Verifică dacă acțiunea a expirat"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class ImageModerationQueue(models.Model):
    """
    Coadă de moderare pentru imagini
    """
    STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('approved', 'Aprobat'),
        ('rejected', 'Respins'),
        ('flagged', 'Marcat pentru verificare'),
    ]
    
    # Imaginea de moderat
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Calea către imagine
    image_path = models.CharField(max_length=500)
    
    # Status moderare
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Verificări automate
    has_faces = models.BooleanField(default=False)
    has_text = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Moderare manuală
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='images_reviewed'
    )
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Imagine în moderare"
        verbose_name_plural = "Imagini în moderare"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Imagine {self.image_path} - {self.get_status_display()}"


# Utility functions for moderation
def check_rate_limit(user, limit_type):
    """
    Verifică și actualizează rate limiting pentru un utilizator
    """
    rate_limit, created = RateLimit.objects.get_or_create(
        user=user,
        limit_type=limit_type,
        defaults={
            'count': 0,
            'window_start': timezone.now()
        }
    )

    if rate_limit.can_perform_action():
        rate_limit.increment_count()
        return True

    return False


def is_ip_blocked(ip_address):
    """
    Verifică dacă un IP este blocat
    """
    blocked_ip = IPBlock.objects.filter(
        ip_address=ip_address
    ).first()

    if blocked_ip:
        return blocked_ip.is_active()

    return False


def block_ip(ip_address, reason='flood', duration_hours=24, user_agent='', blocked_by=None):
    """
    Blochează un IP
    """
    blocked_until = timezone.now() + timedelta(hours=duration_hours) if duration_hours else None

    ip_block, created = IPBlock.objects.get_or_create(
        ip_address=ip_address,
        defaults={
            'reason': reason,
            'blocked_until': blocked_until,
            'user_agent': user_agent,
            'blocked_by': blocked_by,
            'is_permanent': duration_hours is None
        }
    )

    return ip_block


def create_report(reporter, content_object, report_type, description):
    """
    Creează o raportare
    """
    content_type = ContentType.objects.get_for_model(content_object)

    report = Report.objects.create(
        reporter=reporter,
        content_type=content_type,
        object_id=content_object.id,
        report_type=report_type,
        description=description
    )

    return report
