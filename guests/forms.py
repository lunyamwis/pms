from django import forms
from .models import Guest, GuestDocument, GuestReview


class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'email', 'phone', 'whatsapp_number',
                  'gender', 'date_of_birth', 'id_type', 'id_number', 'id_expiry_date',
                  'nationality', 'country_of_residence', 'address',
                  'language_preference', 'is_vip', 'tags', 'notes']
        widgets = {
            f: forms.TextInput(attrs={'class': 'form-control'})
            for f in ['first_name', 'last_name', 'email', 'phone', 'whatsapp_number',
                      'id_number', 'nationality', 'country_of_residence', 'language_preference', 'tags']
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname, field in self.fields.items():
            if not hasattr(field.widget, 'attrs') or 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
        self.fields['date_of_birth'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        self.fields['id_expiry_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        self.fields['address'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        self.fields['notes'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        self.fields['gender'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['id_type'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['is_vip'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})


class GuestSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name, email, phone...'}))
    filter = forms.ChoiceField(
        choices=[('all', 'All'), ('vip', 'VIP'), ('repeat', 'Repeat Guests'), ('blacklisted', 'Blacklisted')],
        required=False, widget=forms.Select(attrs={'class': 'form-control'})
    )


class GuestDocumentForm(forms.ModelForm):
    class Meta:
        model = GuestDocument
        fields = ['document_type', 'file', 'notes']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GuestReviewForm(forms.ModelForm):
    class Meta:
        model = GuestReview
        fields = ['overall_rating', 'cleanliness_rating', 'communication_rating',
                  'rule_adherence_rating', 'comment', 'is_recommended']
        widgets = {
            'overall_rating': forms.Select(attrs={'class': 'form-control'}),
            'cleanliness_rating': forms.Select(attrs={'class': 'form-control'}),
            'communication_rating': forms.Select(attrs={'class': 'form-control'}),
            'rule_adherence_rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_recommended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
