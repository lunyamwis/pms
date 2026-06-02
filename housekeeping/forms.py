from django import forms
from .models import CleaningTask, MaintenanceRequest, RoomServiceOrder, HousekeepingStaff


class CleaningTaskForm(forms.ModelForm):
    class Meta:
        model = CleaningTask
        fields = ['booking_property', 'unit', 'booking', 'assigned_to', 'task_type', 'priority',
                  'scheduled_date', 'scheduled_time', 'estimated_duration_minutes', 'notes']
        widgets = {f: forms.Select(attrs={'class': 'form-control'}) for f in ['booking_property', 'unit', 'booking', 'assigned_to', 'task_type', 'priority']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            if 'class' not in self.fields[f].widget.attrs:
                self.fields[f].widget.attrs['class'] = 'form-control'
        self.fields['scheduled_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        self.fields['scheduled_time'].widget = forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
        self.fields['notes'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['booking_property', 'unit', 'title', 'description', 'category', 'priority', 'reported_by']
        widgets = {
            'booking_property': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'reported_by': forms.TextInput(attrs={'class': 'form-control'}),
        }


class HousekeepingStaffForm(forms.ModelForm):
    class Meta:
        model = HousekeepingStaff
        fields = ['name', 'phone', 'email', 'role', 'properties', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'properties': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
