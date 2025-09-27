from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, CraftsmanProfile, CraftsmanPortfolio, County, City
from services.models import Service, ServiceCategory
from .validators import (
    validate_no_profanity, validate_romanian_phone, validate_strong_password,
    validate_email_format, validate_name, validate_company_name,
    validate_description, validate_services_selection
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
        label='Serviciile pe care le oferi (1-5 servicii)'
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

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password', 'password_confirm', 'county', 'services', 'company_name')

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
                company_name=self.cleaned_data.get('company_name', ''),
                description=f"Meșter specializat în {', '.join([s.name for s in self.cleaned_data['services'][:3]])}"
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
        self.fields['profile_picture'].widget.attrs.update({'class': 'form-control'})
        
        # Update labels to Romanian
        self.fields['first_name'].label = 'Prenume'
        self.fields['last_name'].label = 'Nume'
        self.fields['email'].label = 'Adresa de email'
        self.fields['phone_number'].label = 'Număr de telefon'
        self.fields['profile_picture'].label = 'Poză de profil'


class CraftsmanProfileForm(forms.ModelForm):
    class Meta:
        model = CraftsmanProfile
        fields = (
            'company_name', 'description', 'experience_years', 'hourly_rate',
            'service_radius', 'county', 'city', 'address', 'tax_number', 'is_company'
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
        self.fields['company_name'].label = 'Numele companiei'
        self.fields['description'].label = 'Descriere'
        self.fields['experience_years'].label = 'Ani de experiență'
        self.fields['hourly_rate'].label = 'Tarif pe oră (RON)'
        self.fields['service_radius'].label = 'Raza de serviciu (km)'
        self.fields['county'].label = 'Județul'
        self.fields['city'].label = 'Orașul'
        self.fields['address'].label = 'Adresa'
        self.fields['tax_number'].label = 'CUI/CNP'
        self.fields['is_company'].label = 'Sunt o companie'

        # Set empty labels for select fields
        self.fields['county'].empty_label = 'Selectează județul'
        self.fields['city'].empty_label = 'Selectează orașul'
        
        # Add help text and validation attributes
        self.fields['description'].help_text = 'Descrie-ți serviciile și experiența (maxim 1000 caractere)'
        self.fields['service_radius'].help_text = 'Distanța maximă la care te deplasezi pentru lucrări'

        # Add validation for numeric fields
        self.fields['experience_years'].widget.attrs.update({
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
        self.fields['service_radius'].widget.attrs.update({
            'type': 'number',
            'min': '1',
            'max': '500',
            'placeholder': 'ex. 50'
        })

        # Add validation for text fields
        self.fields['company_name'].widget.attrs.update({
            'maxlength': '200',
            'placeholder': 'ex. SC Construct SRL'
        })
        self.fields['address'].widget.attrs.update({
            'maxlength': '255',
            'placeholder': 'Strada, numărul, etc.'
        })
        self.fields['tax_number'].widget.attrs.update({
            'maxlength': '20',
            'placeholder': 'ex. RO12345678 sau 1234567890123'
        })

        # Make description a textarea with validation
        self.fields['description'].widget = forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'maxlength': '1000',
            'placeholder': 'Descrie-ți serviciile, experiența și specializările...'
        })


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
        self.fields['image'].label = 'Imagine'
        self.fields['title'].label = 'Titlu lucrare'
        self.fields['description'].label = 'Descriere'

        # Make description a textarea
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})


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
