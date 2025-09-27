from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='craftsman_profile')
    company_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=1000, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    service_radius = models.PositiveIntegerField(default=50, help_text="Raza de serviciu în km")

    # Location
    county = models.ForeignKey(County, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=300, blank=True)

    # Business details
    tax_number = models.CharField(max_length=50, blank=True, help_text="CUI/CNP")
    is_company = models.BooleanField(default=False)

    # Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_jobs_completed = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.company_name or 'Meseriaș'}"


class CraftsmanPortfolio(models.Model):
    craftsman = models.ForeignKey(CraftsmanProfile, on_delete=models.CASCADE, related_name='portfolio_images')
    image = models.ImageField(upload_to='portfolio/')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.craftsman.user.username} - {self.title or 'Portfolio Image'}"
