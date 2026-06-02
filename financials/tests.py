from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from financials.models import CashbookEntry, Receipt

User = get_user_model()


def make_user(email='fin@test.com'):
    u = User.objects.create_user(username=email, email=email, password='testpass123')
    u.role = 'agent'
    u.email_verified = True
    u.save()
    return u


class CashbookModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_receipt_entry(self):
        """Can create a receipt (income) entry."""
        e = CashbookEntry.objects.create(
            date=timezone.now().date(), name='Alice', description='1 Bedroom @ 2500',
            entry_type='receipt', category='room_booking', amount=Decimal('2500.00'),
            recorded_by=self.user
        )
        self.assertEqual(e.entry_type, 'receipt')
        self.assertEqual(e.amount, Decimal('2500.00'))

    def test_opening_balance_is_starting_balance(self):
        """Opening balance entry sets initial balance."""
        e = CashbookEntry.objects.create(
            date=timezone.now().date(), name='Opening Balance', description='Balance B/F',
            entry_type='receipt', category='other_income', amount=Decimal('19000.00'),
            is_opening_balance=True, recorded_by=self.user
        )
        self.assertEqual(e.balance, Decimal('19000.00'))

    def test_running_balance_adds_receipt(self):
        """Second receipt entry adds to balance."""
        import datetime
        today = timezone.now().date()
        e1 = CashbookEntry.objects.create(
            date=today, name='Opening', description='B/F',
            entry_type='receipt', category='other_income', amount=Decimal('10000.00'),
            is_opening_balance=True, recorded_by=self.user
        )
        e2 = CashbookEntry.objects.create(
            date=today + datetime.timedelta(days=1), name='Guest',
            description='1 bedroom', entry_type='receipt',
            category='room_booking', amount=Decimal('2500.00'),
            recorded_by=self.user
        )
        e2.refresh_from_db()
        self.assertEqual(e2.balance, Decimal('12500.00'))

    def test_running_balance_subtracts_payment(self):
        """Payment entry reduces balance."""
        import datetime
        today = timezone.now().date()
        e1 = CashbookEntry.objects.create(
            date=today, name='Opening', description='B/F',
            entry_type='receipt', category='other_income', amount=Decimal('10000.00'),
            is_opening_balance=True, recorded_by=self.user
        )
        e2 = CashbookEntry.objects.create(
            date=today + datetime.timedelta(days=1), name='Safaricom',
            description='Internet', entry_type='payment',
            category='internet', amount=Decimal('1500.00'),
            recorded_by=self.user
        )
        e2.refresh_from_db()
        self.assertEqual(e2.balance, Decimal('8500.00'))

    def test_str_representation(self):
        """__str__ includes date, name, type and amount."""
        e = CashbookEntry.objects.create(
            date=timezone.now().date(), name='Test', description='Test entry',
            entry_type='receipt', category='room_booking', amount=Decimal('1000.00'),
            recorded_by=self.user
        )
        s = str(e)
        self.assertIn('Test', s)
        self.assertIn('1000', s)

    def test_opening_balance_flag(self):
        """is_opening_balance can be set."""
        e = CashbookEntry.objects.create(
            date=timezone.now().date(), name='OB', description='B/F',
            entry_type='receipt', category='other_income', amount=Decimal('5000.00'),
            is_opening_balance=True, recorded_by=self.user
        )
        self.assertTrue(e.is_opening_balance)


class ReceiptModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def _make_booking(self):
        from guests.models import Guest
        from properties.models import Property
        from bookings.models import Booking
        guest = Guest.objects.create(first_name='R', last_name='Test', phone='+254700000999')
        prop = Property.objects.create(
            title='R Property', slug='r-property', property_type='apartment',
            listing_type='rent', status='available', price=2500,
            address='Test', city='Nairobi', country='Kenya',
            owner=self.user, bedrooms=1, bathrooms=1, area=30
        )
        import datetime
        today = timezone.now().date()
        return Booking.objects.create(
            asset_property=prop, guest=guest, managed_by=self.user,
            check_in_date=today + datetime.timedelta(days=1),
            check_out_date=today + datetime.timedelta(days=4),
            room_rate=Decimal('2500.00'), source='direct'
        )

    def test_receipt_number_auto_generated(self):
        """Receipt number is auto-generated in RCP-YYYY-NNNN format."""
        booking = self._make_booking()
        r = Receipt.objects.create(
            booking=booking, guest_name='R Test', property_name='R Property',
            check_in_date=booking.check_in_date, check_out_date=booking.check_out_date,
            room_rate=Decimal('2500.00'), total_nights=3,
            subtotal=Decimal('7500.00'), cleaning_fee=Decimal('0'),
            tax_amount=Decimal('0'), discount_amount=Decimal('0'),
            total_amount=Decimal('7500.00'), payment_method='cash', issued_by=self.user
        )
        self.assertTrue(r.receipt_number.startswith('RCP-'))

    def test_receipt_str_representation(self):
        """Receipt __str__ includes receipt number and guest name."""
        booking = self._make_booking()
        r = Receipt.objects.create(
            booking=booking, guest_name='R Test', property_name='R Property',
            check_in_date=booking.check_in_date, check_out_date=booking.check_out_date,
            room_rate=Decimal('2500.00'), total_nights=3,
            subtotal=Decimal('7500.00'), cleaning_fee=Decimal('0'),
            tax_amount=Decimal('0'), discount_amount=Decimal('0'),
            total_amount=Decimal('7500.00'), payment_method='cash', issued_by=self.user
        )
        s = str(r)
        self.assertIn('RCP-', s)
        self.assertIn('R Test', s)


class FinancialViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def test_cashbook_view_200(self):
        resp = self.client.get(reverse('financials:cashbook'))
        self.assertEqual(resp.status_code, 200)

    def test_cashbook_add_entry(self):
        """POST to add_entry creates a CashbookEntry."""
        count = CashbookEntry.objects.count()
        resp = self.client.post(reverse('financials:add_entry'), {
            'date': timezone.now().date(),
            'name': 'John', 'description': '1 bedroom', 'entry_type': 'receipt',
            'category': 'room_booking', 'amount': '2500',
        })
        self.assertEqual(CashbookEntry.objects.count(), count + 1)

    def test_cashbook_export_csv(self):
        resp = self.client.get(reverse('financials:export_cashbook'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp['Content-Type'])

    def test_financial_dashboard_200(self):
        resp = self.client.get(reverse('financials:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_financial_report_200(self):
        resp = self.client.get(reverse('financials:report'))
        self.assertEqual(resp.status_code, 200)

    def test_chart_data_api(self):
        resp = self.client.get(reverse('financials:chart_data'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 7)

    def test_receipt_list_200(self):
        resp = self.client.get(reverse('financials:receipt_list'))
        self.assertEqual(resp.status_code, 200)
