from django import forms
from accounts.models import CustomUser

class AgentProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'profile_picture',
            'bio', 'company_name', 'license_number', 'website',
            'facebook', 'twitter', 'linkedin', 'instagram'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class AgentNotificationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'receive_property_inquiries',
            'receive_review_notifications',
            'receive_message_notifications',
            'receive_property_updates'
        ]

class AgentEmailPreferencesForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'receive_newsletter',
            'receive_marketing_emails',
            'receive_property_alerts',
            'receive_weekly_report'
        ] 