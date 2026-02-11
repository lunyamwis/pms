from django import forms
from django.contrib.auth.forms import UserChangeForm
from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from allauth.account.models import EmailAddress
from .models import SavedSearch

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(validators=[phone_regex], max_length=17, required=False)
    role = forms.ChoiceField(choices=get_user_model().ROLE_CHOICES, required=True)
    newsletter = forms.BooleanField(required=False, initial=True)
    terms = forms.BooleanField(required=True)

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.role = self.cleaned_data['role']
        user.email_newsletter = self.cleaned_data['newsletter']
        
        # Check if email is already verified in allauth
        email_address = EmailAddress.objects.filter(email=user.email).first()
        if email_address and email_address.verified:
            user.email_verified = True
        
        user.save()
        return user

class UserProfileForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email', 'phone', 'bio', 'profile_picture',
                 'website', 'facebook', 'twitter', 'linkedin']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class EmailPreferencesForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email_notifications', 'email_newsletter', 'email_marketing']

class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['show_email', 'show_phone', 'show_address']

class SavedSearchForm(forms.ModelForm):
    class Meta:
        model = SavedSearch
        fields = ['name', 'property_type', 'min_price', 'max_price', 'min_bedrooms',
                 'min_bathrooms', 'min_area', 'max_area', 'location']
        widgets = {
            'min_price': forms.NumberInput(attrs={'placeholder': 'Min Price'}),
            'max_price': forms.NumberInput(attrs={'placeholder': 'Max Price'}),
            'min_bedrooms': forms.NumberInput(attrs={'placeholder': 'Min Bedrooms'}),
            'min_bathrooms': forms.NumberInput(attrs={'placeholder': 'Min Bathrooms'}),
            'min_area': forms.NumberInput(attrs={'placeholder': 'Min Area (sq ft)'}),
            'max_area': forms.NumberInput(attrs={'placeholder': 'Max Area (sq ft)'}),
            'location': forms.TextInput(attrs={'placeholder': 'City, State or ZIP'})
        } 