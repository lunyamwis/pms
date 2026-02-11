from django import forms

class ContactForm(forms.Form):
    INQUIRY_TYPES = (
        ('general', 'General Inquiry'),
        ('property', 'Property Information'),
        ('agent', 'Agent Information'),
        ('appointment', 'Schedule Appointment'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    )

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
        'placeholder': 'Your Phone Number (Optional)'
    }))
    inquiry_type = forms.ChoiceField(choices=INQUIRY_TYPES, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Subject'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Your Message',
        'rows': 5
    }))
    property_id = forms.CharField(max_length=50, required=False, widget=forms.HiddenInput())
    agent_id = forms.CharField(max_length=50, required=False, widget=forms.HiddenInput())
    preferred_contact = forms.ChoiceField(
        choices=[('email', 'Email'), ('phone', 'Phone')],
        widget=forms.RadioSelect,
        initial='email'
    )
    newsletter_signup = forms.BooleanField(
        required=False,
        initial=True,
        label='Sign up for our newsletter to receive property updates'
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if self.cleaned_data.get('preferred_contact') == 'phone' and not phone:
            raise forms.ValidationError('Phone number is required when phone is selected as preferred contact method.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required')
        return email

    def clean(self):
        cleaned_data = super().clean()
        inquiry_type = cleaned_data.get('inquiry_type')
        property_id = cleaned_data.get('property_id')
        agent_id = cleaned_data.get('agent_id')

        if inquiry_type == 'property' and not property_id:
            raise forms.ValidationError('Property ID is required for property inquiries.')
        elif inquiry_type == 'agent' and not agent_id:
            raise forms.ValidationError('Agent ID is required for agent inquiries.')

        return cleaned_data 