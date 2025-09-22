from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, CraftsmanProfile, CraftsmanPortfolio, County


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    
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
    """Simplified registration form similar to MyHammer"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'adresa@email.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Parola'
        })
    )
    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        }),
        empty_label="Alege județul"
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'county')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Un utilizator cu această adresă de email există deja.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.set_password(self.cleaned_data['password'])
        user.user_type = 'client'
        if commit:
            user.save()
        return user


class SimpleCraftsmanRegistrationForm(forms.ModelForm):
    """Simplified craftsman registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'adresa@email.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Parola'
        })
    )
    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        }),
        empty_label="Alege județul"
    )
    trade = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'ex. Tâmplar, Electrician, Instalator'
        }),
        label='Meseria principală'
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'county', 'trade')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Un utilizator cu această adresă de email există deja.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.set_password(self.cleaned_data['password'])
        user.user_type = 'craftsman'
        if commit:
            user.save()
            # Create craftsman profile
            CraftsmanProfile.objects.create(
                user=user,
                county=self.cleaned_data['county'],
                description=f"Meșter {self.cleaned_data['trade']}"
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
        
        # Add help text
        self.fields['description'].help_text = 'Descrie-ți serviciile și experiența (maxim 1000 caractere)'
        self.fields['service_radius'].help_text = 'Distanța maximă la care te deplasezi pentru lucrări'
        
        # Make description a textarea
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})


class CraftsmanPortfolioForm(forms.ModelForm):
    """Form for uploading portfolio images"""
    class Meta:
        model = CraftsmanPortfolio
        fields = ('image', 'title', 'description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes
        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ex. Renovare baie modernă'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descrie lucrarea realizată...'
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
