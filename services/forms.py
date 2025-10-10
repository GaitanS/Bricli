from django import forms
from django.core.exceptions import ValidationError

from accounts.models import County

from .models import CraftsmanService, Order, OrderImage, Quote, Review, ReviewImage


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
    """Form for creating new orders"""

    preferred_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data preferată (opțional)",
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
    """Form for uploading multiple review images"""

    image1 = forms.ImageField(required=False, label="Imagine 1")
    image2 = forms.ImageField(required=False, label="Imagine 2")
    image3 = forms.ImageField(required=False, label="Imagine 3")
    image4 = forms.ImageField(required=False, label="Imagine 4")
    image5 = forms.ImageField(required=False, label="Imagine 5")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["image1", "image2", "image3", "image4", "image5"]:
            self.fields[field_name].widget.attrs.update({"class": "form-control", "accept": "image/*"})

    def clean(self):
        """Validate and optimize all uploaded images"""
        from accounts.utils import optimize_review_image

        cleaned_data = super().clean()

        for field_name in ["image1", "image2", "image3", "image4", "image5"]:
            image = cleaned_data.get(field_name)
            if image:
                # Check file size (max 10MB)
                if image.size > 10 * 1024 * 1024:
                    raise forms.ValidationError(f"{field_name}: Imaginea este prea mare. Dimensiunea maximă este 10MB.")

                # Check file type
                if not image.content_type.startswith("image/"):
                    raise forms.ValidationError(f"{field_name}: Fișierul trebuie să fie o imagine.")

                # Optimize the image
                cleaned_data[field_name] = optimize_review_image(image)

        return cleaned_data

    def get_images(self):
        """Return list of uploaded images"""
        images = []
        for field_name in ["image1", "image2", "image3", "image4", "image5"]:
            image = self.cleaned_data.get(field_name)
            if image:
                images.append(image)
        return images


class QuoteForm(forms.ModelForm):
    """Form for craftsmen to submit quotes"""

    class Meta:
        model = Quote
        fields = ("price", "description", "estimated_duration")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})

        # Update labels to Romanian
        self.fields["price"].label = "Preț ofertat (RON)"
        self.fields["description"].label = "Descrierea ofertei"
        self.fields["estimated_duration"].label = "Durata estimată"

        # Add placeholders and validation attributes
        self.fields["price"].widget.attrs.update(
            {
                "type": "number",
                "placeholder": "ex. 1500",
                "step": "0.01",
                "min": "1",
                "max": "1000000",
                "required": True,
            }
        )
        self.fields["description"].widget.attrs.update(
            {
                "placeholder": "Descrie ce include oferta ta...",
                "rows": 4,
                "required": True,
                "minlength": "20",
                "maxlength": "1000",
            }
        )
        self.fields["estimated_duration"].widget.attrs.update(
            {"placeholder": "ex. 3-5 zile lucrătoare", "required": True, "maxlength": "100"}
        )

        # Make description a textarea
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 4, "class": "form-control"})

        # Add help text
        self.fields["price"].help_text = "Prețul final pentru întreaga lucrare"
        self.fields["description"].help_text = "Explică ce include prețul și cum vei realiza lucrarea"


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
