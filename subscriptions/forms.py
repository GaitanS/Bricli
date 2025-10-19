"""
Subscription Forms

Forms for fiscal data collection, subscription management, and cancellation.
"""

from django import forms
from accounts.models import CraftsmanProfile, County


class FiscalDataForm(forms.ModelForm):
    """
    Form for collecting fiscal data required for invoice generation.

    Required fields vary based on fiscal_type:
    - PF (Persoană Fizică): CNP
    - PFA/SRL: CUI, company_name
    """

    class Meta:
        model = CraftsmanProfile
        fields = [
            'fiscal_type',
            'cui',
            'cnp',
            'company_name',
            'fiscal_address_street',
            'fiscal_address_city',
            'fiscal_address_county',
            'fiscal_address_postal_code',
            'phone',
        ]
        widgets = {
            'fiscal_type': forms.Select(attrs={'class': 'form-control'}),
            'cui': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RO12345678 (doar pentru PFA/SRL)'
            }),
            'cnp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234567890123 (doar pentru PF)',
                'maxlength': '13'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SC Compania SRL (doar pentru PFA/SRL)'
            }),
            'fiscal_address_street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Strada Exemplu, nr. 10, Bloc A, Ap. 5'
            }),
            'fiscal_address_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'București'
            }),
            'fiscal_address_county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'București'
            }),
            'fiscal_address_postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '010101',
                'maxlength': '6'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+40712345678'
            }),
        }
        labels = {
            'fiscal_type': 'Tip persoană',
            'cui': 'CUI',
            'cnp': 'CNP',
            'company_name': 'Denumire firmă',
            'fiscal_address_street': 'Adresă (strada, număr, bloc, apartament)',
            'fiscal_address_city': 'Oraș',
            'fiscal_address_county': 'Județ',
            'fiscal_address_postal_code': 'Cod poștal',
            'phone': 'Telefon',
        }
        help_texts = {
            'fiscal_type': 'Selectează tipul de persoană (PF = Persoană Fizică, PFA = Persoană Fizică Autorizată, SRL = Societate cu Răspundere Limitată)',
            'cui': 'Codul Unic de Înregistrare (obligatoriu pentru PFA și SRL)',
            'cnp': 'Codul Numeric Personal (obligatoriu pentru Persoană Fizică)',
            'company_name': 'Denumirea companiei (obligatoriu pentru PFA și SRL)',
            'phone': 'Număr de telefon în format +40XXXXXXXXX',
        }

    def clean_cui(self):
        """Validate CUI format"""
        cui = self.cleaned_data.get('cui', '').strip()
        fiscal_type = self.cleaned_data.get('fiscal_type')

        if fiscal_type in ['PFA', 'SRL'] and not cui:
            raise forms.ValidationError('CUI este obligatoriu pentru PFA și SRL.')

        if cui:
            # Remove RO prefix if present
            cui = cui.upper().replace('RO', '')
            # Check if numeric
            if not cui.isdigit():
                raise forms.ValidationError('CUI trebuie să conțină doar cifre (eventual prefixat cu RO).')
            # Check length (2-10 digits typically)
            if len(cui) < 2 or len(cui) > 10:
                raise forms.ValidationError('CUI trebuie să aibă între 2 și 10 cifre.')

        return cui

    def clean_cnp(self):
        """Validate CNP format"""
        cnp = self.cleaned_data.get('cnp', '').strip()
        fiscal_type = self.cleaned_data.get('fiscal_type')

        if fiscal_type == 'PF' and not cnp:
            raise forms.ValidationError('CNP este obligatoriu pentru Persoană Fizică.')

        if cnp:
            # Check if numeric
            if not cnp.isdigit():
                raise forms.ValidationError('CNP trebuie să conțină doar cifre.')
            # Check length (13 digits)
            if len(cnp) != 13:
                raise forms.ValidationError('CNP trebuie să aibă exact 13 cifre.')

        return cnp

    def clean_company_name(self):
        """Validate company name"""
        company_name = self.cleaned_data.get('company_name', '').strip()
        fiscal_type = self.cleaned_data.get('fiscal_type')

        if fiscal_type in ['PFA', 'SRL'] and not company_name:
            raise forms.ValidationError('Denumirea firmei este obligatorie pentru PFA și SRL.')

        return company_name

    def clean_phone(self):
        """Validate and normalize phone number to +40XXXXXXXXX format"""
        phone = self.cleaned_data.get('phone', '').strip()

        if not phone:
            raise forms.ValidationError('Numărul de telefon este obligatoriu.')

        # Remove spaces, dashes, parentheses
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Handle different formats
        if phone.startswith('+40'):
            # Already in correct format
            pass
        elif phone.startswith('0040'):
            # Replace 0040 with +40
            phone = '+40' + phone[4:]
        elif phone.startswith('40'):
            # Add + prefix
            phone = '+' + phone
        elif phone.startswith('07') or phone.startswith('02') or phone.startswith('03'):
            # Romanian mobile/landline starting with 0
            phone = '+40' + phone[1:]
        else:
            raise forms.ValidationError('Format invalid. Folosește formatul +40XXXXXXXXX sau 07XXXXXXXX.')

        # Validate final format: +40 followed by 9 digits
        if not phone.startswith('+40'):
            raise forms.ValidationError('Numărul trebuie să înceapă cu +40.')

        digits_only = phone[3:]  # Remove +40
        if not digits_only.isdigit() or len(digits_only) != 9:
            raise forms.ValidationError('După +40 trebuie să urmeze exact 9 cifre.')

        return phone

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        fiscal_type = cleaned_data.get('fiscal_type')

        # Ensure required fields are present based on fiscal_type
        if fiscal_type == 'PF':
            if not cleaned_data.get('cnp'):
                self.add_error('cnp', 'CNP este obligatoriu pentru Persoană Fizică.')
        elif fiscal_type in ['PFA', 'SRL']:
            if not cleaned_data.get('cui'):
                self.add_error('cui', 'CUI este obligatoriu pentru PFA și SRL.')
            if not cleaned_data.get('company_name'):
                self.add_error('company_name', 'Denumirea firmei este obligatorie pentru PFA și SRL.')

        return cleaned_data


class UpgradeConfirmationForm(forms.Form):
    """
    Form for confirming upgrade and withdrawal right waiver.

    Required by OUG 34/2014 for online contracts.
    """

    waive_withdrawal_right = forms.BooleanField(
        required=True,
        label='Accept renunțarea la dreptul de retragere',
        help_text=(
            'Conform OUG 34/2014, ai dreptul de a te retrage din acest contract în termen de 14 zile. '
            'Bifând această căsuță, îți exprimi acordul explicit ca serviciul să înceapă imediat și '
            'renunți la dreptul de retragere pentru perioada deja consumată.'
        ),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    agree_terms = forms.BooleanField(
        required=True,
        label='Accept Termenii și Condițiile',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    payment_method_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )


class CancelSubscriptionForm(forms.Form):
    """
    Form for confirming subscription cancellation.
    """

    confirm_cancellation = forms.BooleanField(
        required=True,
        label='Confirm că doresc să anulez abonamentul',
        help_text='Abonamentul va rămâne activ până la sfârșitul perioadei de facturare curente.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    reason = forms.ChoiceField(
        required=False,
        label='Motivul anulării (opțional)',
        choices=[
            ('', 'Selectează un motiv (opțional)'),
            ('too_expensive', 'Prea scump'),
            ('not_enough_leads', 'Nu primesc destule lead-uri'),
            ('poor_quality', 'Lead-urile nu sunt de calitate'),
            ('switching_service', 'Trec la alt serviciu'),
            ('business_closed', 'Închid afacerea'),
            ('other', 'Altele'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    feedback = forms.CharField(
        required=False,
        label='Feedback (opțional)',
        help_text='Spune-ne cum putem să ne îmbunătățim serviciile.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Feedback-ul tău ne ajută să îmbunătățim serviciul...'
        })
    )


class RequestRefundForm(forms.Form):
    """
    Form for requesting refund within 14-day withdrawal period.
    """

    confirm_refund = forms.BooleanField(
        required=True,
        label='Confirm că doresc rambursarea sumei plătite',
        help_text=(
            'Vei primi suma plătită înapoi pe cardul folosit la plată în 5-7 zile lucrătoare. '
            'Abonamentul va fi retrogradat imediat la Plan Gratuit (5 lead-uri/lună).'
        ),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    reason = forms.CharField(
        required=False,
        label='Motivul rambursării (opțional)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'De ce dorești rambursarea?'
        })
    )
