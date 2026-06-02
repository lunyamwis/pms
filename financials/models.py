from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum

User = get_user_model()


class CashbookEntry(models.Model):
    ENTRY_TYPE_CHOICES = [
        ('receipt', 'Receipt (Income)'),
        ('payment', 'Payment (Expense)'),
    ]

    CATEGORY_CHOICES = [
        ('room_booking', 'Room Booking'),
        ('management_fee', 'Management Fee'),
        ('other_income', 'Other Income'),
        ('rent_expense', 'Rent/Lease'),
        ('internet', 'Internet'),
        ('cleaning', 'Cleaning'),
        ('supplies', 'Supplies'),
        ('furniture', 'Furniture & Equipment'),
        ('maintenance', 'Maintenance & Repairs'),
        ('salary', 'Salary/Wages'),
        ('utilities', 'Utilities'),
        ('marketing', 'Marketing'),
        ('other_expense', 'Other Expense'),
    ]

    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=500)
    name = models.CharField(max_length=200, help_text='Payer or payee name')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='room_booking')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    booking_property = models.ForeignKey(
        'properties.Property', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cashbook_entries'
    )
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cashbook_entries'
    )
    reference = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_opening_balance = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cashbook_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'created_at']
        verbose_name = 'Cashbook Entry'
        verbose_name_plural = 'Cashbook Entries'

    def __str__(self):
        return f"{self.date} | {self.name} | {self.entry_type} | {self.amount}"

    def get_absolute_url(self):
        return reverse('financials:cashbook')

    def save(self, *args, **kwargs):
        # Compute running balance
        prev = CashbookEntry.objects.filter(
            date__lt=self.date
        ).order_by('-date', '-created_at').first()
        if not prev:
            prev_same_day = CashbookEntry.objects.filter(
                date=self.date
            ).exclude(pk=self.pk).order_by('-created_at').first()
            prev_balance = prev_same_day.balance if prev_same_day else 0
        else:
            prev_balance = prev.balance

        if self.entry_type == 'receipt':
            self.balance = prev_balance + self.amount
        else:
            self.balance = prev_balance - self.amount

        super().save(*args, **kwargs)

        # Update balances of all subsequent entries
        subsequent = CashbookEntry.objects.filter(
            date__gte=self.date
        ).exclude(pk=self.pk).order_by('date', 'created_at')
        running = self.balance
        for entry in subsequent:
            if entry.entry_type == 'receipt':
                running = running + entry.amount
            else:
                running = running - entry.amount
            CashbookEntry.objects.filter(pk=entry.pk).update(balance=running)


class Receipt(models.Model):
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.PROTECT, related_name='receipts'
    )
    guest_name = models.CharField(max_length=200)
    property_name = models.CharField(max_length=200)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    room_rate = models.DecimalField(max_digits=10, decimal_places=2)
    total_nights = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    cleaning_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    pdf_file = models.FileField(upload_to='receipts/%Y/%m/', null=True, blank=True)
    sent_via_email = models.BooleanField(default=False)
    sent_via_whatsapp = models.BooleanField(default=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-issued_at']

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = timezone.now().year
            count = Receipt.objects.filter(issued_at__year=year).count() + 1
            self.receipt_number = f"RCP-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} - {self.guest_name}"

    def get_absolute_url(self):
        return reverse('financials:receipt_detail', kwargs={'pk': self.pk})


class Budget(models.Model):
    CATEGORY_CHOICES = CashbookEntry.CATEGORY_CHOICES

    booking_property = models.ForeignKey(
        'properties.Property', on_delete=models.CASCADE, related_name='budgets'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    budgeted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['booking_property', 'period_start', 'period_end', 'category']

    def __str__(self):
        return f"{self.property} - {self.category} - {self.period_start}"

    @property
    def actual_amount(self):
        return CashbookEntry.objects.filter(
            property=self.property,
            date__range=[self.period_start, self.period_end],
            category=self.category,
        ).aggregate(total=Sum('amount'))['total'] or 0

    @property
    def variance(self):
        return self.budgeted_amount - self.actual_amount
