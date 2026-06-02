from django import forms
from django.utils import timezone
from .models import CashbookEntry, Receipt, Budget


class CashbookEntryForm(forms.ModelForm):
    class Meta:
        model = CashbookEntry
        fields = ['date','name','description','entry_type','category','amount','asset_property' ,'payment_method','reference','notes']
        widgets = {
            'date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Payer/Payee name'}),
            'description': forms.TextInput(attrs={'class':'form-control'}),
            'entry_type': forms.Select(attrs={'class':'form-control'}),
            'category': forms.Select(attrs={'class':'form-control'}),
            'amount': forms.NumberInput(attrs={'class':'form-control','step':'0.01','min':'0.01'}),
            'asset_property' : forms.Select(attrs={'class':'form-control'}),
            'payment_method': forms.TextInput(attrs={'class':'form-control','placeholder':'Cash, M-Pesa, Bank...'}),
            'reference': forms.TextInput(attrs={'class':'form-control'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':2}),
        }


class DateRangeForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','class':'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','class':'form-control'}))
    category = forms.ChoiceField(
        choices=[('','All Categories')] + CashbookEntry.CATEGORY_CHOICES,
        required=False, widget=forms.Select(attrs={'class':'form-control'})
    )


class OpeningBalanceForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type':'date','class':'form-control'}))
    amount = forms.DecimalField(max_digits=14, decimal_places=2, widget=forms.NumberInput(attrs={'class':'form-control','step':'0.01'}))
