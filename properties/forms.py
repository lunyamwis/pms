from django import forms
from django.core.validators import MinValueValidator
from .models import Property, PropertyImage, PropertyReview

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class PropertySearchForm(forms.Form):
    PRICE_CHOICES = [
        ('', 'Any Price'),
        ('0-100000', 'Under $100,000'),
        ('100000-200000', '$100,000 - $200,000'),
        ('200000-300000', '$200,000 - $300,000'),
        ('300000-500000', '$300,000 - $500,000'),
        ('500000-750000', '$500,000 - $750,000'),
        ('750000-1000000', '$750,000 - $1,000,000'),
        ('1000000-plus', '$1,000,000+'),
    ]

    BEDROOM_CHOICES = [
        ('', 'Any'),
        ('1', '1+'),
        ('2', '2+'),
        ('3', '3+'),
        ('4', '4+'),
        ('5', '5+'),
    ]

    BATHROOM_CHOICES = [
        ('', 'Any'),
        ('1', '1+'),
        ('1.5', '1.5+'),
        ('2', '2+'),
        ('3', '3+'),
        ('4', '4+'),
    ]

    keyword = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Enter keywords...',
        'class': 'form-control'
    }))
    
    property_type = forms.ChoiceField(choices=Property.PROPERTY_TYPE_CHOICES, required=False, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    
    listing_type = forms.ChoiceField(choices=Property.LISTING_TYPE_CHOICES, required=False, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    
    price_range = forms.ChoiceField(choices=PRICE_CHOICES, required=False, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    
    bedrooms = forms.ChoiceField(choices=BEDROOM_CHOICES, required=False, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    
    bathrooms = forms.ChoiceField(choices=BATHROOM_CHOICES, required=False, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    
    min_area = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'placeholder': 'Min Area (sqft)',
        'class': 'form-control'
    }))
    
    max_area = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'placeholder': 'Max Area (sqft)',
        'class': 'form-control'
    }))
    
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Enter location...',
        'class': 'form-control'
    }))

    def clean(self):
        cleaned_data = super().clean()
        min_area = cleaned_data.get('min_area')
        max_area = cleaned_data.get('max_area')

        if min_area and max_area and min_area > max_area:
            raise forms.ValidationError("Minimum area cannot be greater than maximum area.")

        return cleaned_data

class PropertyForm(forms.ModelForm):
    # Additional fields for gallery images
    gallery_images = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        help_text='Select multiple images for the property gallery (optional)'
    )

    class Meta:
        model = Property
        exclude = ['slug', 'owner', 'agent', 'views_count', 'favorited_by', 'created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter property title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the property'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'listing_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter area in square feet'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.5'}),
            'garage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'year_built': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year built'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ZIP code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country'}),
            'features': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'amenities': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'main_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter video URL'}),
            'virtual_tour_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter virtual tour URL'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def clean_area(self):
        area = self.cleaned_data.get('area')
        if area and area < 0:
            raise forms.ValidationError("Area cannot be negative.")
        return area

    def clean_main_image(self):
        main_image = self.cleaned_data.get('main_image')
        if main_image:
            # Check if it's a new file being uploaded
            if hasattr(main_image, 'content_type') and not main_image.content_type.startswith('image/'):
                raise forms.ValidationError("Please upload a valid image file.")
            # Check file size - limit to 5MB
            if hasattr(main_image, 'size') and main_image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
        elif not self.instance.pk:  # If it's a new property
            raise forms.ValidationError("Main image is required.")
        return main_image

    def clean_gallery_images(self):
        gallery_images = self.files.getlist('gallery_images')
        if gallery_images:
            for image in gallery_images:
                if not image.content_type.startswith('image/'):
                    raise forms.ValidationError(f"File {image.name} is not a valid image.")
                if image.size > 5 * 1024 * 1024:  # 5MB limit
                    raise forms.ValidationError(f"Image {image.name} is too large (>5MB).")
        return gallery_images

class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PropertyReviewForm(forms.ModelForm):
    class Meta:
        model = PropertyReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating and (rating < 1 or rating > 5):
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating

class PropertyInquiryForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your Name'
    }))
    
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your Email'
    }))
    
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your Phone Number'
    }))
    
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 4,
        'placeholder': 'Your Message'
    }))
    
    preferred_contact = forms.ChoiceField(choices=[('email', 'Email'), ('phone', 'Phone')], widget=forms.RadioSelect(attrs={
        'class': 'form-check-input'
    })) 