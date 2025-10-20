from django import forms
from django.core.exceptions import ValidationError

from accounts.models import County

from .models import CraftsmanService, Order, OrderImage, Quote, QuoteAttachment, Review, ReviewImage, validate_quote_attachment


class OrderImageForm(forms.ModelForm):
    class Meta:
        model = OrderImage
        fields = ["image", "description"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "description": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Descriere opțională pentru imagine"}
            ),
        }


class OrderForm(forms.ModelForm):
    """Form for creating new orders (cu suport pentru utilizatori neautentificați)"""

    preferred_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data preferată (opțional)",
    )

    # Câmpuri de autentificare (doar pentru utilizatori neautentificați)
    user_name = forms.CharField(
        required=False,
        max_length=100,
        label="Nume complet",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex. Ion Popescu",
            "data-auth-field": "true"
        })
    )

    user_email = forms.EmailField(
        required=False,
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "ex. ion.popescu@email.com",
            "data-auth-field": "true",
            "id": "id_user_email"
        })
    )

    user_phone = forms.CharField(
        required=False,
        max_length=15,
        label="Telefon (opțional, dar recomandat)",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex. 0740123456",
            "data-auth-field": "true",
            "pattern": "^(07|\\+407)\\d{8}$"
        }),
        help_text="Format: 0740123456 sau +40740123456"
    )

    user_password = forms.CharField(
        required=False,
        min_length=8,
        label="Parolă",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Minim 8 caractere",
            "data-auth-field": "true",
            "id": "id_user_password"
        })
    )

    user_password_confirm = forms.CharField(
        required=False,
        label="Confirmă parola",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Reintroduceți parola",
            "data-auth-field": "true",
            "id": "id_user_password_confirm"
        })
    )

    verification_method = forms.ChoiceField(
        required=False,
        choices=[('email', 'Email'), ('whatsapp', 'WhatsApp')],
        initial='email',
        label="Primește codul de verificare pe:",
        widget=forms.RadioSelect(attrs={"data-auth-field": "true"})
    )

    class Meta:
        model = Order
        fields = (
            "title",
            "description",
            "service",
            "county",
            "city",
            "address",
            "budget_min",
            "budget_max",
            "urgency",
            "preferred_date",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({"class": "form-select"})
            elif isinstance(self.fields[field].widget, forms.DateInput):
                self.fields[field].widget.attrs.update({"class": "form-control", "type": "date"})
            else:
                self.fields[field].widget.attrs.update({"class": "form-control"})

        # Update labels to Romanian
        self.fields["title"].label = "Titlu comandă"
        self.fields["description"].label = "Descriere detaliată"
        self.fields["service"].label = "Serviciu"
        self.fields["county"].label = "Județ"
        self.fields["city"].label = "Oraș"
        self.fields["address"].label = "Unde este localizată lucrarea?"
        self.fields["address"].required = True
        self.fields["budget_min"].label = "Buget minim (RON)"
        self.fields["budget_max"].label = "Buget maxim (RON)"
        self.fields["urgency"].label = "Urgență"
        self.fields["preferred_date"].label = "Data preferată"

        # Set empty labels for select fields
        self.fields["service"].empty_label = "Selectează serviciul"
        self.fields["county"].empty_label = "Selectează județul"
        self.fields["city"].empty_label = "Selectează orașul"
        self.fields["urgency"].empty_label = "Selectează urgența"

        # Add placeholders and validation attributes
        self.fields["title"].widget.attrs.update(
            {"placeholder": "ex. Renovare baie completă", "required": True, "minlength": "5", "maxlength": "200"}
        )
        self.fields["description"].widget.attrs.update(
            {
                "placeholder": "Descrie în detaliu ce lucrări ai nevoie...",
                "rows": 4,
                "required": True,
                "minlength": "20",
                "maxlength": "2000",
            }
        )
        self.fields["address"].widget.attrs.update(
            {"placeholder": "Strada, numărul, etajul, apartamentul, etc.", "maxlength": "300", "required": True}
        )

        # Add validation for budget fields
        self.fields["budget_min"].widget.attrs.update(
            {"type": "number", "min": "1", "max": "1000000", "step": "1", "placeholder": "ex. 500"}
        )
        self.fields["budget_max"].widget.attrs.update(
            {"type": "number", "min": "1", "max": "1000000", "step": "1", "placeholder": "ex. 1500"}
        )

        # Add validation for preferred date
        self.fields["preferred_date"].widget.attrs.update({"type": "date", "min": "2025-01-01", "max": "2026-12-31"})

        # Make description a textarea
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 4, "class": "form-control"})

    def clean_user_phone(self):
        """Validare format telefon românesc"""
        phone = self.cleaned_data.get('user_phone')
        if phone:
            import re
            # Remove spaces and dashes
            clean_phone = re.sub(r'[\s\-]', '', phone)
            # Validate Romanian phone format
            if not re.match(r'^(07|\+407)\d{8}$', clean_phone):
                raise ValidationError("Formatul telefonului nu este valid. Folosește formatul 0740123456 sau +40740123456")
        return phone

    def clean(self):
        """Validare câmpuri de autentificare pentru utilizatori neautentificați"""
        cleaned_data = super().clean()

        # Dacă utilizatorul este autentificat, ignoră validarea câmpurilor auth
        # (verificare făcută în view)

        user_email = cleaned_data.get('user_email')
        user_name = cleaned_data.get('user_name')
        user_password = cleaned_data.get('user_password')
        user_password_confirm = cleaned_data.get('user_password_confirm')

        # Dacă sunt completate câmpuri auth, validăm
        if user_email or user_name or user_password:
            # Email obligatoriu pentru utilizatori noi
            if not user_email:
                self.add_error('user_email', 'Emailul este obligatoriu pentru a crea un cont.')

            # Nume obligatoriu
            if not user_name:
                self.add_error('user_name', 'Numele complet este obligatoriu.')

            # Parolă obligatorie
            if not user_password:
                self.add_error('user_password', 'Parola este obligatorie.')

            # Verificare parolele match
            if user_password and user_password_confirm:
                if user_password != user_password_confirm:
                    self.add_error('user_password_confirm', 'Parolele nu coincid.')

            # Verificare lungime parolă
            if user_password and len(user_password) < 8:
                self.add_error('user_password', 'Parola trebuie să aibă minim 8 caractere.')

        return cleaned_data


class ReviewForm(forms.ModelForm):
    """Form for creating reviews"""

    class Meta:
        model = Review
        fields = ("rating", "comment", "quality_rating", "punctuality_rating", "communication_rating")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes and Romanian labels
        self.fields["rating"].label = "Rating general"
        self.fields["comment"].label = "Comentariu"
        self.fields["quality_rating"].label = "Calitatea lucrării"
        self.fields["punctuality_rating"].label = "Punctualitate"
        self.fields["communication_rating"].label = "Comunicare"

        # Style rating fields as star selectors
        for field_name in ["rating", "quality_rating", "punctuality_rating", "communication_rating"]:
            self.fields[field_name].widget = forms.RadioSelect(
                choices=[(i, f'{i} {"stea" if i == 1 else "stele"}') for i in range(1, 6)],
                attrs={"class": "star-rating"},
            )

        # Style comment field
        self.fields["comment"].widget = forms.Textarea(
            attrs={"class": "form-control", "rows": 4, "placeholder": "Scrie despre experiența ta cu acest meșter..."}
        )

        # Make detailed ratings optional but encourage them
        self.fields["quality_rating"].required = False
        self.fields["punctuality_rating"].required = False
        self.fields["communication_rating"].required = False

        # Add help text
        self.fields["comment"].help_text = "Comentariul tău va ajuta alți clienți să ia o decizie informată."


class ReviewImageForm(forms.ModelForm):
    """Form for uploading review images"""

    class Meta:
        model = ReviewImage
        fields = ("image", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["image"].label = "Imagine"
        self.fields["description"].label = "Descriere imagine"

        self.fields["image"].widget.attrs.update({"class": "form-control", "accept": "image/*"})
        self.fields["description"].widget.attrs.update(
            {"class": "form-control", "placeholder": "ex. Lucrarea finalizată, înainte și după, etc."}
        )

    def clean_image(self):
        """Validate and optimize review image"""
        from accounts.utils import optimize_review_image

        image = self.cleaned_data.get("image")
        if image:
            # Check file size (max 10MB)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Imaginea este prea mare. Dimensiunea maximă este 10MB.")

            # Check file type
            if not image.content_type.startswith("image/"):
                raise forms.ValidationError("Fișierul trebuie să fie o imagine.")

            # Optimize the image
            image = optimize_review_image(image)

        return image


class MultipleReviewImageForm(forms.Form):
    """Form for uploading multiple review images (max 5)"""

    # Dummy field to make Django consider the form valid
    # The actual validation happens in clean()
    images = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.max_images = kwargs.pop('max_images', 5)
        self.existing_images_count = kwargs.pop('existing_images_count', 0)
        # Store files for validation
        self.uploaded_files = kwargs.pop('files', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate all uploaded images"""
        from accounts.utils import optimize_review_image

        cleaned_data = super().clean()

        if not self.uploaded_files:
            return cleaned_data

        images = self.uploaded_files.getlist('images')

        # Check maximum number of images
        if len(images) > self.max_images:
            raise forms.ValidationError(
                f"Poți încărca maximum {self.max_images} imagini. Ai selectat {len(images)}."
            )

        # Check total images including existing ones
        total_images = len(images) + self.existing_images_count
        if total_images > self.max_images:
            remaining = self.max_images - self.existing_images_count
            raise forms.ValidationError(
                f"Poți adăuga maximum {remaining} imagini noi (ai deja {self.existing_images_count})."
            )

        # Validate each image
        optimized_images = []
        for idx, image in enumerate(images, start=1):
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    f"Imaginea #{idx} este prea mare. Dimensiunea maximă este 5MB. "
                    f"Dimensiunea ta: {image.size / (1024 * 1024):.1f}MB"
                )

            # Check file type
            if not image.content_type.startswith("image/"):
                raise forms.ValidationError(
                    f"Fișierul #{idx} nu este o imagine validă. Tip: {image.content_type}"
                )

            # Optimize the image
            try:
                optimized_image = optimize_review_image(image)
                optimized_images.append(optimized_image)
            except Exception as e:
                raise forms.ValidationError(
                    f"Eroare la procesarea imaginii #{idx}: {str(e)}"
                )

        cleaned_data['images'] = optimized_images
        return cleaned_data

    def get_images(self):
        """Return list of uploaded and optimized images"""
        return self.cleaned_data.get('images', [])


class QuoteForm(forms.ModelForm):
    """Form for craftsmen to submit quotes - Simplified version with inline duration"""

    # Custom field: duration value (number input)
    duration_value = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=365,
        label="Durată Estimată",
        widget=forms.NumberInput(attrs={
            "class": "form-control duration-input",
            "placeholder": "ex: 5",
            "min": "1",
            "max": "365"
        })
    )

    # Custom field: duration unit (dropdown)
    duration_unit = forms.ChoiceField(
        required=True,
        choices=[
            ('hours', 'Ore'),
            ('days', 'Zile'),
            ('weeks', 'Săptămâni'),
            ('months', 'Luni'),
        ],
        label="",  # No label - inline with input
        widget=forms.Select(attrs={
            "class": "form-select duration-unit"
        })
    )

    # Optional PDF attachment
    pdf_attachment = forms.FileField(
        required=False,
        label="Atașează Ofertă PDF (Opțional)",
        help_text="Poți atașa un document PDF cu oferta ta detaliată (max 5MB)",
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "accept": ".pdf,application/pdf"
        })
    )

    class Meta:
        model = Quote
        fields = ("price", "proposed_start_date", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Price field
        self.fields["price"].label = "Preț Ofertă"
        self.fields["price"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "type": "number",
            "placeholder": "Ex: 1500",
            "step": "0.01",
            "min": "1",
            "required": True,
        })
        self.fields["price"].help_text = "Prețul final pentru întreaga lucrare"

        # Proposed start date
        self.fields["proposed_start_date"].label = "Data propusă de tine"
        self.fields["proposed_start_date"].required = False
        self.fields["proposed_start_date"].widget.attrs.update({
            "type": "date",
            "class": "form-control"
        })
        self.fields["proposed_start_date"].help_text = "Când propui să începi această lucrare"

        # Description
        self.fields["description"].label = "Descrierea Ofertei"
        self.fields["description"].widget = forms.Textarea(attrs={
            "rows": 6,
            "class": "form-control",
            "placeholder": "Descrie în detaliu cum vei realiza lucrarea...",
            "required": True,
            "minlength": "20",
        })
        self.fields["description"].help_text = "Explică ce include prețul și cum vei realiza lucrarea"

        # Pre-populate duration fields if editing
        if self.instance and self.instance.pk:
            if self.instance.duration_value:
                self.initial['duration_value'] = self.instance.duration_value
            if self.instance.duration_unit:
                self.initial['duration_unit'] = self.instance.duration_unit

    def clean_pdf_attachment(self):
        """Validate PDF file"""
        pdf_file = self.cleaned_data.get('pdf_attachment')

        if pdf_file:
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if pdf_file.size > max_size:
                raise forms.ValidationError(
                    f"Fișierul este prea mare ({pdf_file.size / 1024 / 1024:.1f}MB). "
                    f"Dimensiunea maximă permisă este 5MB."
                )

            # Check file extension
            if not pdf_file.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Doar fișiere PDF sunt permise.")

            # Check MIME type
            if pdf_file.content_type not in ['application/pdf', 'application/x-pdf']:
                raise forms.ValidationError("Tipul fișierului nu este PDF valid.")

        return pdf_file

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set duration fields from form
        instance.duration_value = self.cleaned_data['duration_value']
        instance.duration_unit = self.cleaned_data['duration_unit']

        # estimated_duration will be auto-generated in model's save()

        if commit:
            instance.save()

            # Handle PDF attachment if provided
            pdf_file = self.cleaned_data.get('pdf_attachment')
            if pdf_file:
                from .models import QuoteAttachment
                QuoteAttachment.objects.create(
                    quote=instance,
                    file=pdf_file,
                    file_type='pdf',
                    file_size=pdf_file.size,
                    description='Ofertă PDF'
                )

        return instance


class OrderSearchForm(forms.Form):
    """Form for searching orders"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Caută comenzi..."}),
        label="Căutare",
    )

    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        required=False,
        empty_label="Toate județele",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Județ",
    )

    urgency = forms.ChoiceField(
        choices=[("", "Orice urgență")] + Order.URGENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Urgență",
    )

    budget_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Buget minim"}),
        label="Buget minim (RON)",
    )

    budget_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Buget maxim"}),
        label="Buget maxim (RON)",
    )


class CraftsmanServiceForm(forms.ModelForm):
    """Form for craftsmen to add/edit their services"""

    class Meta:
        model = CraftsmanService
        fields = ("service", "price_from", "price_to", "price_unit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({"class": "form-select"})
            else:
                self.fields[field].widget.attrs.update({"class": "form-control"})

        # Update labels to Romanian
        self.fields["service"].label = "Serviciu"
        self.fields["price_from"].label = "Preț de la (RON)"
        self.fields["price_to"].label = "Preț până la (RON)"
        self.fields["price_unit"].label = "Unitate de măsură"

        # Set empty labels
        self.fields["service"].empty_label = "Selectează serviciul"

        # Add placeholders and validation
        self.fields["price_from"].widget.attrs.update(
            {"type": "number", "placeholder": "ex. 50", "step": "0.01", "min": "0", "max": "100000"}
        )
        self.fields["price_to"].widget.attrs.update(
            {"type": "number", "placeholder": "ex. 150", "step": "0.01", "min": "0", "max": "100000"}
        )
        self.fields["price_unit"].widget.attrs.update(
            {"placeholder": "ex. per oră, per mp, per bucată", "maxlength": "50"}
        )

        # Add help text
        self.fields["price_from"].help_text = "Prețul minim pentru acest serviciu"
        self.fields["price_to"].help_text = "Prețul maxim pentru acest serviciu (opțional)"
        self.fields["price_unit"].help_text = "Cum se calculează prețul (ex: per oră, per mp)"

        # Make some fields optional
        self.fields["price_to"].required = False
        self.fields["price_unit"].required = False

    def clean(self):
        cleaned_data = super().clean()
        price_from = cleaned_data.get("price_from")
        price_to = cleaned_data.get("price_to")

        if price_from and price_to and price_from >= price_to:
            raise ValidationError("Prețul maxim trebuie să fie mai mare decât prețul minim.")

        return cleaned_data


class QuoteAttachmentForm(forms.ModelForm):
    """Form pentru adăugare atașamente la oferte"""

    class Meta:
        model = QuoteAttachment
        fields = ["file", "description"]
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx",
                    "class": "form-control",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descriere fișier (opțional)",
                    "maxlength": "200",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["file"].label = "Fișier"
        self.fields["description"].label = "Descriere"
        self.fields["description"].required = False

        self.fields["file"].help_text = "PDF, imagini (JPG, PNG, GIF), documente (DOC, DOCX) - Max 5MB"

    def clean_file(self):
        """Validează tip și mărime fișier"""
        file = self.cleaned_data.get("file")
        if file:
            # Apelează funcția de validare din models.py
            file = validate_quote_attachment(file)
        return file
