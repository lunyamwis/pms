from django import forms
from django.utils import timezone
from .models import Booking, BookingPayment, BookingNote
from guests.models import Guest
from properties.models import Property, PropertyUnit


class BookingForm(forms.ModelForm):
    check_in_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    check_out_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model = Booking
        fields = [
            'booking_property', 'unit', 'guest', 'check_in_date', 'check_out_date',
            'num_adults', 'num_children', 'room_rate', 'cleaning_fee',
            'service_fee', 'tax_amount', 'discount_amount', 'deposit_amount',
            'deposit_paid', 'source', 'external_booking_id',
            'special_requests', 'internal_notes',
        ]
        widgets = {
            'booking_property': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'guest': forms.Select(attrs={'class': 'form-control'}),
            'num_adults': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'num_children': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'room_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cleaning_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'service_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'source': forms.Select(attrs={'class': 'form-control'}),
            'external_booking_id': forms.TextInput(attrs={'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in_date')
        check_out = cleaned_data.get('check_out_date')
        if check_in and check_out:
            if check_out <= check_in:
                raise forms.ValidationError('Check-out date must be after check-in date.')
            if check_in < timezone.now().date():
                raise forms.ValidationError('Check-in date cannot be in the past.')
        return cleaned_data


class CheckInForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in_time', 'internal_notes']
        widgets = {
            'check_in_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CheckOutForm(forms.ModelForm):
    condition_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False, label='Condition Notes'
    )

    class Meta:
        model = Booking
        fields = ['check_out_time']
        widgets = {
            'check_out_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = BookingPayment
        fields = ['payment_method', 'amount', 'reference_number', 'paid_at', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'paid_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class BookingNoteForm(forms.ModelForm):
    class Meta:
        model = BookingNote
        fields = ['note', 'is_private']
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a note...'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BookingSearchForm(forms.Form):
    SORT_CHOICES = [
        ('-created_at', 'Newest First'), ('check_in_date', 'Check-in Date'),
        ('-check_in_date', 'Check-in Date (desc)'), ('total_amount', 'Amount'),
    ]
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guest name, reference...'}))
    status = forms.MultipleChoiceField(choices=Booking.STATUS_CHOICES, required=False, widget=forms.CheckboxSelectMultiple)
    source = forms.ChoiceField(choices=[('', 'All Sources')] + Booking.SOURCE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
