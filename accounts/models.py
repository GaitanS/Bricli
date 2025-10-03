from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import secrets
import pyotp
from django.utils import timezone


class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('client', 'Client'),
        ('craftsman', 'Meseriaș'),
    ]

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='client')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Numărul de telefon trebuie să fie valid.")],
        blank=True
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    # Two-Factor Authentication fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def get_whatsapp_link(self):
        """Generate WhatsApp link from phone number"""
        if self.phone_number:
            # Remove any non-digit characters and format for WhatsApp
            clean_number = ''.join(filter(str.isdigit, self.phone_number))
            if clean_number.startswith('0'):
                # Romanian number starting with 0, replace with +40
                clean_number = '40' + clean_number[1:]
            elif not clean_number.startswith('40'):
                # Add Romanian country code if not present
                clean_number = '40' + clean_number
            return f"https://wa.me/{clean_number}"
        return None

    def get_formatted_phone(self):
        """Get formatted phone number for display"""
        if self.phone_number:
            clean_number = ''.join(filter(str.isdigit, self.phone_number))
            if len(clean_number) >= 10:
                if clean_number.startswith('40'):
                    # Format as +40 XXX XXX XXX
                    return f"+40 {clean_number[2:5]} {clean_number[5:8]} {clean_number[8:]}"
                elif clean_number.startswith('0'):
                    # Format as 0XXX XXX XXX
                    return f"{clean_number[:4]} {clean_number[4:7]} {clean_number[7:]}"
            return self.phone_number
        return None

    def generate_2fa_secret(self):
        """Generate a new 2FA secret key"""
        if not self.two_factor_secret:
            self.two_factor_secret = pyotp.random_base32()
            self.save()
        return self.two_factor_secret

    def get_2fa_qr_code_url(self):
        """Get QR code URL for 2FA setup"""
        if not self.two_factor_secret:
            self.generate_2fa_secret()
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(
            name=self.email,
            issuer_name="Bricli"
        )

    def verify_2fa_token(self, token):
        """Verify a 2FA token"""
        if not self.two_factor_enabled or not self.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self):
        """Generate new backup codes for 2FA"""
        codes = []
        for _ in range(8):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        
        self.backup_codes = codes
        self.save()
        return codes

    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            self.save()
            return True
        return False

    def disable_2fa(self):
        """Disable 2FA for the user"""
        self.two_factor_enabled = False
        self.two_factor_secret = None
        self.backup_codes = []
        self.save()


class County(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)  # RO county codes

    class Meta:
        verbose_name_plural = "Counties"
        ordering = ['name']

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='cities')
    postal_code = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']
        unique_together = ['name', 'county']

    def __str__(self):
        return f"{self.name}, {self.county.name}"


class CraftsmanProfile(models.Model):
    """
    Profil meșter redesigned pentru protecția datelor și profesionalism.
    Câmpuri obligatorii: display_name, city/county, coverage_radius_km, categories, bio, profile_photo, portfolio (min 3 poze)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='craftsman_profile')

    # CÂMPURI OBLIGATORII (temporar opționale pentru migrație)
    display_name = models.CharField(
        max_length=100,
        blank=True, null=True,
        help_text="Nume afișat (nume persoană sau denumire comercială)"
    )

    # Locație obligatorie (temporar opțională pentru migrație)
    county = models.ForeignKey(County, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)

    # Raza de acoperire obligatorie (5-150 km)
    coverage_radius_km = models.PositiveSmallIntegerField(
        default=25,
        help_text="Raza de acoperire în km (5-150)"
    )

    # Descriere obligatorie (min 200 caractere) (temporar opțională pentru migrație)
    bio = models.TextField(
        blank=True, null=True,
        help_text="Descriere scurtă - ce tip de lucrări faci (minim 200 caractere)"
    )

    # Poză de profil obligatorie (temporar opțională pentru migrație)
    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True, null=True,
        help_text="Poză de profil"
    )

    # CÂMPURI OPȚIONALE (dar utile pentru clienți)
    years_experience = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Ani de experiență"
    )

    # Tarife orientative
    hourly_rate = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Tarif orientativ (lei/oră)"
    )

    min_job_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Valoare minimă lucrare (lei)"
    )

    # Informații firmă (opțional)
    company_cui = models.CharField(
        max_length=20, blank=True,
        help_text="CUI/CIF (dacă e firmă/PFA) - pentru badge 'Firmă înregistrată'"
    )
    company_verified_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Data verificării CUI (setat automat)"
    )

    # Linkuri publice (opțional)
    website_url = models.URLField(blank=True, help_text="Site web")
    facebook_url = models.URLField(blank=True, help_text="Facebook")
    instagram_url = models.URLField(blank=True, help_text="Instagram")

    # SISTEM DE RATING ȘI REPUTAȚIE
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_jobs_completed = models.PositiveIntegerField(default=0)

    # CALCULARE COMPLETARE PROFIL (0-100%)
    profile_completion = models.PositiveSmallIntegerField(default=0)

    # BADGE-URI AUTOMATE
    is_profile_complete = models.BooleanField(default=False)
    is_company_verified = models.BooleanField(default=False)
    is_top_rated = models.BooleanField(default=False)  # ≥4.5 rating cu min reviews
    is_active = models.BooleanField(default=False)  # După 3 joburi finalizate
    is_trusted = models.BooleanField(default=False)  # După 10 recenzii verificate

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Meșter"
        verbose_name_plural = "Profile Meșteri"

    def __str__(self):
        city_name = self.city.name if self.city else "Necunoscut"
        county_name = self.county.name if self.county else "Necunoscut"
        return f"{self.display_name} - {city_name}, {county_name}"

    def calculate_profile_completion(self):
        """Calculează procentajul de completare a profilului (0-100%)"""
        score = 0
        total_points = 100

        # Câmpuri obligatorii (60 puncte total)
        if self.display_name:
            score += 10
        if self.county and self.city:
            score += 10
        if self.coverage_radius_km and 5 <= self.coverage_radius_km <= 150:
            score += 10
        if self.bio and len(self.bio.strip()) >= 200:
            score += 15
        if self.profile_photo:
            score += 15

        # Portfolio (min 3 poze) - 20 puncte
        # Verifică dacă profilul are un ID (a fost salvat) înainte de a accesa portfolio_images
        if self.pk:
            portfolio_count = self.portfolio_images.count()
            if portfolio_count >= 3:
                score += 20
            elif portfolio_count > 0:
                score += (portfolio_count * 20) // 3

        # Servicii/categorii (10 puncte)
        # Verifică dacă profilul are un ID înainte de a accesa serviciile
        if self.pk and hasattr(self, 'services') and self.services.exists():
            score += 10

        # Câmpuri opționale (10 puncte total)
        if self.years_experience:
            score += 3
        if self.hourly_rate or self.min_job_value:
            score += 3
        if self.website_url or self.facebook_url or self.instagram_url:
            score += 2
        if self.company_cui:
            score += 2

        return min(score, total_points)

    def update_profile_completion(self):
        """Actualizează procentajul de completare și badge-urile"""
        self.profile_completion = self.calculate_profile_completion()
        self.is_profile_complete = self.profile_completion == 100

        # Update badge-uri
        self.update_badges()

        # Salvează fără a declanșa din nou save()
        CraftsmanProfile.objects.filter(pk=self.pk).update(
            profile_completion=self.profile_completion,
            is_profile_complete=self.is_profile_complete,
            is_company_verified=self.is_company_verified,
            is_top_rated=self.is_top_rated,
            is_active=self.is_active,
            is_trusted=self.is_trusted
        )

    def update_badges(self):
        """Actualizează badge-urile bazate pe criterii"""
        # Badge "Firmă înregistrată" - CUI validat
        self.is_company_verified = bool(self.company_cui and self.company_verified_at)

        # Badge "Top Rated" - rating ≥4.5 cu minim 5 recenzii
        self.is_top_rated = (
            self.average_rating >= 4.5 and
            self.total_reviews >= 5
        )

        # Badge "Activ" - după primele 3 joburi finalizate
        self.is_active = self.total_jobs_completed >= 3

        # Badge "De încredere" - după 10 recenzii verificate
        self.is_trusted = self.total_reviews >= 10

    def can_bid_on_jobs(self):
        """Verifică dacă meșterul poate licita (profil complet)"""
        return (
            self.is_profile_complete and
            self.profile_photo and
            self.portfolio_images.count() >= 3 and
            len(self.bio.strip()) >= 200 and
            self.coverage_radius_km
        )

    def get_badges(self):
        """Returnează lista de badge-uri active"""
        badges = []

        if self.is_profile_complete:
            badges.append({
                'name': 'Profil complet',
                'icon': 'fas fa-check-circle',
                'color': 'success',
                'description': '100% profil completat'
            })

        if self.is_company_verified:
            badges.append({
                'name': 'Firmă înregistrată',
                'icon': 'fas fa-building',
                'color': 'primary',
                'description': 'CUI validat automat'
            })

        if self.is_top_rated:
            badges.append({
                'name': 'Top Rated',
                'icon': 'fas fa-star',
                'color': 'warning',
                'description': f'Rating {self.average_rating} cu {self.total_reviews} recenzii'
            })

        if self.is_active:
            badges.append({
                'name': 'Activ',
                'icon': 'fas fa-bolt',
                'color': 'info',
                'description': f'{self.total_jobs_completed} lucrări finalizate'
            })

        if self.is_trusted:
            badges.append({
                'name': 'De încredere',
                'icon': 'fas fa-shield-alt',
                'color': 'success',
                'description': f'{self.total_reviews} recenzii verificate'
            })

        return badges

    def save(self, *args, **kwargs):
        # Calculează completarea profilului la fiecare salvare
        self.profile_completion = self.calculate_profile_completion()
        self.is_profile_complete = self.profile_completion == 100
        self.update_badges()

        super().save(*args, **kwargs)


class CraftsmanPortfolio(models.Model):
    """
    Portofoliu meșter - minim 3 poze obligatorii pentru profil complet.
    Fără fețe/PII vizibile - doar lucrări.
    """
    craftsman = models.ForeignKey(
        CraftsmanProfile,
        on_delete=models.CASCADE,
        related_name='portfolio_images'
    )

    image = models.ImageField(
        upload_to='portfolio/%Y/%m/',
        help_text="Poză cu lucrarea (fără fețe/date personale vizibile)"
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Titlu lucrare (opțional)"
    )

    description = models.TextField(
        max_length=500,
        blank=True,
        help_text="Descriere lucrare (opțional)"
    )

    # Moderare automată
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Imagine Portofoliu"
        verbose_name_plural = "Imagini Portofoliu"

    def __str__(self):
        return f"{self.craftsman.display_name} - {self.title or 'Imagine Portofoliu'}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizează completarea profilului meșterului
        self.craftsman.update_profile_completion()
