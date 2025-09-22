from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderImage, Quote, Review, ReviewImage
from accounts.models import County, City


class OrderForm(forms.ModelForm):
    """Form for creating new orders"""
    class Meta:
        model = Order
        fields = (
            'title', 'description', 'service', 'county', 'city', 'address',
            'budget_min', 'budget_max', 'urgency', 'preferred_date'
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            elif isinstance(self.fields[field].widget, forms.DateInput):
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'type': 'date'
                })
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Update labels to Romanian
        self.fields['title'].label = 'Titlu comandă'
        self.fields['description'].label = 'Descriere detaliată'
        self.fields['service'].label = 'Serviciu'
        self.fields['county'].label = 'Județ'
        self.fields['city'].label = 'Oraș'
        self.fields['address'].label = 'Adresă (opțional)'
        self.fields['budget_min'].label = 'Buget minim (RON)'
        self.fields['budget_max'].label = 'Buget maxim (RON)'
        self.fields['urgency'].label = 'Urgență'
        self.fields['preferred_date'].label = 'Data preferată'
        
        # Add placeholders
        self.fields['title'].widget.attrs.update({
            'placeholder': 'ex. Renovare baie completă'
        })
        self.fields['description'].widget.attrs.update({
            'placeholder': 'Descrie în detaliu ce lucrări ai nevoie...',
            'rows': 4
        })
        self.fields['address'].widget.attrs.update({
            'placeholder': 'Strada, numărul, etc.'
        })
        
        # Make description a textarea
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})


class ReviewForm(forms.ModelForm):
    """Form for creating reviews"""
    class Meta:
        model = Review
        fields = ('rating', 'comment', 'quality_rating', 'punctuality_rating', 'communication_rating')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes and Romanian labels
        self.fields['rating'].label = 'Rating general'
        self.fields['comment'].label = 'Comentariu'
        self.fields['quality_rating'].label = 'Calitatea lucrării'
        self.fields['punctuality_rating'].label = 'Punctualitate'
        self.fields['communication_rating'].label = 'Comunicare'
        
        # Style rating fields as star selectors
        for field_name in ['rating', 'quality_rating', 'punctuality_rating', 'communication_rating']:
            self.fields[field_name].widget = forms.RadioSelect(
                choices=[(i, f'{i} {"stea" if i == 1 else "stele"}') for i in range(1, 6)],
                attrs={'class': 'star-rating'}
            )
        
        # Style comment field
        self.fields['comment'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Scrie despre experiența ta cu acest meșter...'
        })
        
        # Make detailed ratings optional but encourage them
        self.fields['quality_rating'].required = False
        self.fields['punctuality_rating'].required = False
        self.fields['communication_rating'].required = False
        
        # Add help text
        self.fields['comment'].help_text = 'Comentariul tău va ajuta alți clienți să ia o decizie informată.'


class ReviewImageForm(forms.ModelForm):
    """Form for uploading review images"""
    class Meta:
        model = ReviewImage
        fields = ('image', 'description')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['image'].label = 'Imagine'
        self.fields['description'].label = 'Descriere imagine'
        
        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ex. Lucrarea finalizată, înainte și după, etc.'
        })


class MultipleReviewImageForm(forms.Form):
    """Form for uploading multiple review images"""
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


class QuoteForm(forms.ModelForm):
    """Form for craftsmen to submit quotes"""
    class Meta:
        model = Quote
        fields = ('price', 'description', 'estimated_duration')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Update labels to Romanian
        self.fields['price'].label = 'Preț ofertat (RON)'
        self.fields['description'].label = 'Descrierea ofertei'
        self.fields['estimated_duration'].label = 'Durata estimată'
        
        # Add placeholders
        self.fields['price'].widget.attrs.update({
            'placeholder': 'ex. 1500',
            'step': '0.01'
        })
        self.fields['description'].widget.attrs.update({
            'placeholder': 'Descrie ce include oferta ta...',
            'rows': 4
        })
        self.fields['estimated_duration'].widget.attrs.update({
            'placeholder': 'ex. 3-5 zile lucrătoare'
        })
        
        # Make description a textarea
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})
        
        # Add help text
        self.fields['price'].help_text = 'Prețul final pentru întreaga lucrare'
        self.fields['description'].help_text = 'Explică ce include prețul și cum vei realiza lucrarea'


class OrderSearchForm(forms.Form):
    """Form for searching orders"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Caută comenzi...'
        }),
        label='Căutare'
    )
    
    county = forms.ModelChoiceField(
        queryset=County.objects.all(),
        required=False,
        empty_label='Toate județele',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Județ'
    )
    
    urgency = forms.ChoiceField(
        choices=[('', 'Orice urgență')] + Order.URGENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Urgență'
    )
    
    budget_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buget minim'
        }),
        label='Buget minim (RON)'
    )
    
    budget_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buget maxim'
        }),
        label='Buget maxim (RON)'
    )
