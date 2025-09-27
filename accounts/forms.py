from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, CraftsmanProfile, CraftsmanPortfolio, County, City
from services.models import Service, ServiceCategory
from .validators import (
    validate_no_profanity, validate_romanian_phone, validate_strong_password,
    validate_email_format, validate_name, validate_company_name,
    validate_description, validate_services_selection, validate_display_name,
    validate_coverage_radius, validate_bio_length, validate_hourly_rate,
    validate_min_job_value
)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'adresa@email.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Prenume',
            'pattern': r'[A-Za-zÀ-ÿ\s]+',
            'title': 'Doar litere și spații sunt permise'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nume',
            'pattern': r'[A-Za-zÀ-ÿ\s]+',
            'title': 'Doar litere și spații sunt permise'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'pattern': r'[0-9+\-\s\(\)]+',
            'placeholder': 'ex. 0721234567'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Update labels to Romanian
        self.fields['username'].label = 'Nume utilizator'
        self.fields['email'].label = 'Adresa de email'
        self.fields['first_name'].label = 'Prenume'
        self.fields['last_name'].label = 'Nume'
        self.fields['phone_number'].label = 'Număr de telefon'
        self.fields['password1'].label = 'Parola'
        self.fields['password2'].label = 'Confirmă parola'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Un utilizator cu această adresă de email există deja.')
        return email


class SimpleUserRegistrationForm(forms.ModelForm):
    """Enhanced client registration form with validation"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Prenume'
        }),
        label='Prenume'
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nume de familie'
        }),
        label='Nume de familie'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'adresa@email.com'
        }),
        label='Adresa de email'
    )

    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0721234567 (opțional)',
            'type': 'tel'
        }),
        label='Număr de telefon (opțional)'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Parola (min. 8 caractere)'
        }),
        label='Parola'
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirmă parola'
        }),
        label='Confirmă parola'
    )

    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        }),
        empty_label="Alege județul",
        label='Județul'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password', 'password_confirm', 'county')

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        validate_name(first_name)
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        validate_name(last_name)
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validate_email_format(email)

        if User.objects.filter(email=email).exists():
            raise ValidationError('Un utilizator cu această adresă de email există deja.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:  # Opțional pentru clienți
            validate_romanian_phone(phone_number)

            if User.objects.filter(phone_number=phone_number).exists():
                raise ValidationError('Un utilizator cu acest număr de telefon există deja.')
        return phone_number

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_strong_password(password)
        return password

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError('Parolele nu se potrivesc.')
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.set_password(self.cleaned_data['password'])
        user.user_type = 'client'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')

        if commit:
            user.save()
        return user


class SimpleCraftsmanRegistrationForm(forms.ModelForm):
    """Enhanced craftsman registration form with multiple services selection"""

    # Informații personale
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Prenume'
        }),
        label='Prenume'
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nume de familie'
        }),
        label='Nume de familie'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'adresa@email.com'
        }),
        label='Adresa de email'
    )

    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0721234567',
            'type': 'tel'
        }),
        label='Număr de telefon'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Parola (min. 8 caractere)'
        }),
        label='Parola'
    )

    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirmă parola'
        }),
        label='Confirmă parola'
    )

    # Locație
    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        }),
        empty_label="Alege județul",
        label='Județul'
    )

    # Servicii (selecție multiplă)
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True).select_related('category'),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Serviciile pe care le oferi (1-10 servicii)'
    )

    # Informații opționale
    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Numele companiei (opțional)'
        }),
        label='Numele companiei (opțional)'
    )

    bio = forms.CharField(
        max_length=2000,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-lg',
            'rows': 4,
            'placeholder': 'Descrie-ți serviciile, experiența și ce te face special. Minim 200 caractere...'
        }),
        label='Prezintă-te clienților'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password', 'password_confirm', 'county', 'services', 'company_name', 'bio')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Grupează serviciile pe categorii pentru afișare mai bună
        services_by_category = {}
        for service in Service.objects.filter(is_active=True).select_related('category'):
            category_name = service.category.name
            if category_name not in services_by_category:
                services_by_category[category_name] = []
            services_by_category[category_name].append(service)

        self.services_by_category = services_by_category

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        validate_name(first_name)
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        validate_name(last_name)
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        validate_email_format(email)

        if User.objects.filter(email=email).exists():
            raise ValidationError('Un utilizator cu această adresă de email există deja.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        validate_romanian_phone(phone_number)

        if User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError('Un utilizator cu acest număr de telefon există deja.')
        return phone_number

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_strong_password(password)
        return password

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError('Parolele nu se potrivesc.')
        return password_confirm

    def clean_services(self):
        services = self.cleaned_data.get('services')
        validate_services_selection(services)
        return services

    def clean_company_name(self):
        company_name = self.cleaned_data.get('company_name')
        if company_name:
            validate_company_name(company_name)
        return company_name

    def clean_bio(self):
        from .validators import validate_bio_length
        bio = self.cleaned_data.get('bio')
        validate_bio_length(bio)
        return bio

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.set_password(self.cleaned_data['password'])
        user.user_type = 'craftsman'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']

        if commit:
            user.save()

            # Create craftsman profile
            craftsman_profile = CraftsmanProfile.objects.create(
                user=user,
                county=self.cleaned_data['county'],
                bio=self.cleaned_data.get('bio', '')
            )

            # Add selected services
            from services.models import CraftsmanService
            for service in self.cleaned_data['services']:
                CraftsmanService.objects.create(
                    craftsman=craftsman_profile,
                    service=service
                )

        return user


class CraftsmanRegistrationForm(UserRegistrationForm):
    company_name = forms.CharField(max_length=200, required=False, label='Numele companiei (opțional)')
    
    class Meta(UserRegistrationForm.Meta):
        fields = UserRegistrationForm.Meta.fields + ('company_name',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_name'].widget.attrs.update({'class': 'form-control'})


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['profile_picture'].widget = forms.FileInput(attrs={
            'class': 'form-control',
            'style': 'display: none;',
            'accept': 'image/*'
        })

        # Update labels to Romanian
        self.fields['first_name'].label = 'Prenume'
        self.fields['last_name'].label = 'Nume'
        self.fields['email'].label = 'Adresa de email'
        self.fields['phone_number'].label = 'Număr de telefon'
        self.fields['profile_picture'].label = ''


class CraftsmanProfileForm(forms.ModelForm):
    """Formular pentru profilul meșterului cu noua structură"""

    class Meta:
        model = CraftsmanProfile
        fields = (
            'display_name', 'county', 'city', 'coverage_radius_km', 'bio',
            'profile_photo', 'years_experience', 'hourly_rate', 'min_job_value',
            'company_cui', 'website_url', 'facebook_url', 'instagram_url'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Update labels to Romanian
        self.fields['display_name'].label = 'Nume afișat'
        self.fields['county'].label = 'Județul'
        self.fields['city'].label = 'Orașul'
        self.fields['coverage_radius_km'].label = 'Raza de acoperire (km)'
        self.fields['bio'].label = 'Descrierea ta profesională'
        self.fields['profile_photo'].label = 'Poză de profil'
        self.fields['years_experience'].label = 'Ani de experiență (opțional)'
        self.fields['hourly_rate'].label = 'Tarif orientativ pe oră (RON) - opțional'
        self.fields['min_job_value'].label = 'Valoarea minimă lucrare (RON) - opțional'
        self.fields['company_cui'].label = 'CUI/CIF (opțional)'
        self.fields['website_url'].label = 'Site web (opțional)'
        self.fields['facebook_url'].label = 'Facebook (opțional)'
        self.fields['instagram_url'].label = 'Instagram (opțional)'

        # Set empty labels for select fields
        self.fields['county'].empty_label = 'Selectează județul'
        self.fields['city'].empty_label = 'Selectează orașul'
        
        # Add help text and validation attributes
        self.fields['display_name'].help_text = 'Numele sub care vei apărea pe platformă (nume persoană sau denumire comercială)'
        self.fields['coverage_radius_km'].help_text = 'Distanța maximă la care te deplasezi pentru lucrări (5-150 km)'
        self.fields['bio'].help_text = 'Descrie-ți serviciile și experiența (minim 200 caractere)'
        self.fields['profile_photo'].help_text = 'Poză de profil profesională'
        self.fields['company_cui'].help_text = 'Pentru badge "Firmă înregistrată" - va fi verificat automat'

        # Add validation for numeric fields
        self.fields['years_experience'].widget.attrs.update({
            'type': 'number',
            'min': '0',
            'max': '50',
            'placeholder': 'ex. 5'
        })
        self.fields['hourly_rate'].widget.attrs.update({
            'type': 'number',
            'min': '10',
            'max': '1000',
            'step': '0.01',
            'placeholder': 'ex. 50.00'
        })
        self.fields['min_job_value'].widget.attrs.update({
            'type': 'number',
            'min': '50',
            'max': '100000',
            'step': '0.01',
            'placeholder': 'ex. 200.00'
        })
        self.fields['coverage_radius_km'].widget.attrs.update({
            'type': 'number',
            'min': '5',
            'max': '150',
            'placeholder': 'ex. 25'
        })

        # Add validation for text fields
        self.fields['display_name'].widget.attrs.update({
            'maxlength': '100',
            'placeholder': 'ex. Ion Popescu sau SC Construct SRL'
        })
        self.fields['company_cui'].widget.attrs.update({
            'maxlength': '20',
            'placeholder': 'ex. RO12345678'
        })

        # URL fields
        self.fields['website_url'].widget.attrs.update({
            'placeholder': 'https://www.site-ul-tau.ro'
        })
        self.fields['facebook_url'].widget.attrs.update({
            'placeholder': 'https://facebook.com/pagina-ta'
        })
        self.fields['instagram_url'].widget.attrs.update({
            'placeholder': 'https://instagram.com/contul-tau'
        })

        # Make bio a textarea with validation
        self.fields['bio'].widget = forms.Textarea(attrs={
            'rows': 5,
            'class': 'form-control',
            'maxlength': '2000',
            'placeholder': 'Descrie-ți serviciile, experiența și ce te face special. Minim 200 caractere...'
        })

        # Profile photo field
        self.fields['profile_photo'].widget.attrs.update({
            'accept': 'image/*'
        })

    def clean_display_name(self):
        display_name = self.cleaned_data.get('display_name')
        validate_display_name(display_name)
        return display_name

    def clean_coverage_radius_km(self):
        radius = self.cleaned_data.get('coverage_radius_km')
        validate_coverage_radius(radius)
        return radius

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        validate_bio_length(bio)
        return bio

    def clean_company_cui(self):
        cui = self.cleaned_data.get('company_cui')
        if cui:
            validate_cui_format(cui)
        return cui

    def clean_hourly_rate(self):
        rate = self.cleaned_data.get('hourly_rate')
        if rate:
            validate_hourly_rate(rate)
        return rate

    def clean_min_job_value(self):
        value = self.cleaned_data.get('min_job_value')
        if value:
            validate_min_job_value(value)
        return value

    def clean_website_url(self):
        url = self.cleaned_data.get('website_url')
        if url:
            validate_url_format(url)
        return url

    def clean_facebook_url(self):
        url = self.cleaned_data.get('facebook_url')
        if url:
            validate_url_format(url)
        return url

    def clean_instagram_url(self):
        url = self.cleaned_data.get('instagram_url')
        if url:
            validate_url_format(url)
        return url

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            validate_portfolio_image(photo)
        return photo


class CraftsmanPortfolioForm(forms.ModelForm):
    """Form for uploading portfolio images"""
    class Meta:
        model = CraftsmanPortfolio
        fields = ('image', 'title', 'description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes and validation attributes
        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*',
            'required': True
        })
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ex. Renovare baie modernă',
            'required': True,
            'minlength': '5',
            'maxlength': '100'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descrie lucrarea realizată...',
            'maxlength': '500'
        })

        # Update labels to Romanian
        self.fields['image'].label = 'Imagine lucrare'
        self.fields['title'].label = 'Titlu lucrare (opțional)'
        self.fields['description'].label = 'Descriere lucrare (opțional)'

        # Make description a textarea
        self.fields['description'].widget = forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Descrie lucrarea realizată...'
        })

        # Add help text
        self.fields['image'].help_text = 'Poză cu lucrarea (fără fețe/date personale vizibile). Max 5MB.'
        self.fields['title'].help_text = 'Numele lucrării (ex: Renovare baie modernă)'
        self.fields['description'].help_text = 'Detalii despre lucrarea realizată'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        validate_portfolio_image(image)
        return image

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            validate_no_profanity(title)
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            validate_no_profanity(description)
        return description


class BulkPortfolioUploadForm(forms.Form):
    """Form for uploading multiple portfolio images at once"""
    image1 = forms.ImageField(required=False, label='Imagine 1')
    image2 = forms.ImageField(required=False, label='Imagine 2')
    image3 = forms.ImageField(required=False, label='Imagine 3')
    image4 = forms.ImageField(required=False, label='Imagine 4')
    image5 = forms.ImageField(required=False, label='Imagine 5')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['image1', 'image2', 'image3', 'image4', 'image5']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control',
                'accept': 'image/*'
            })

    def get_images(self):
        """Return list of uploaded images"""
        images = []
        for field_name in ['image1', 'image2', 'image3', 'image4', 'image5']:
            image = self.cleaned_data.get(field_name)
            if image:
                images.append(image)
        return images


class CraftsmanSkillsForm(forms.Form):
    """Form for selecting craftsman skills and specializations"""
    SKILL_CHOICES = [
        ('electrician', 'Electrician'),
        ('instalator', 'Instalator'),
        ('tamplar', 'Tâmplar'),
        ('zugrav', 'Zugrav'),
        ('zidar', 'Zidar'),
        ('acoperisuri', 'Acoperișuri'),
        ('gradinarit', 'Grădinărit'),
        ('curatenie', 'Curățenie'),
        ('transport', 'Transport'),
        ('it', 'IT'),
        ('auto', 'Reparații Auto'),
        ('design', 'Design Interior'),
        ('parchet', 'Parchet și Gresie'),
        ('metalice', 'Lucrări Metalice'),
        ('sticlarie', 'Sticlărie'),
        ('tapiterie', 'Tapițerie'),
        ('seminee', 'Șeminee și Coșuri'),
        ('piscine', 'Piscine'),
        ('pavaje', 'Pavaje și Alei'),
        ('demolari', 'Demolări'),
        ('incalzire', 'Instalații Încălzire'),
        ('geamuri', 'Geamuri și Ferestre'),
        ('renovari', 'Renovări și Construcții'),
        ('mutari', 'Mutări'),
        ('asamblare', 'Asamblare și Montaj'),
    ]

    primary_skill = forms.ChoiceField(
        choices=SKILL_CHOICES,
        label='Meseria principală',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    secondary_skills = forms.MultipleChoiceField(
        choices=SKILL_CHOICES,
        required=False,
        label='Meserii secundare',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text='Selectează alte meserii pe care le practici'
    )

    certifications = forms.CharField(
        required=False,
        label='Certificări și autorizații',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'ex. Autorizație electrician, Certificat sudor, etc.'
        }),
        help_text='Listează certificările și autorizațiile pe care le deții'
    )
