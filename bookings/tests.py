from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import datetime

from bookings.models import Booking, BookingPayment, BookingMessage, BookingNote

User = get_user_model()


_cnt = [0]


def make_user(email=None, password='testpass123', role='agent'):
    _cnt[0] += 1
    email = email or f'mgr{_cnt[0]}@test.com'
    u = User.objects.create_user(
        username=email, email=email, password=password,
        first_name='Test', last_name='Manager'
    )
    u.role = role
    u.email_verified = True
    u.save()
    return u


def make_guest():
    _cnt[0] += 1
    from guests.models import Guest
    return Guest.objects.create(
        first_name='Jane', last_name='Doe',
        phone=f'+25470000{_cnt[0]:04d}', whatsapp_number=f'+25470000{_cnt[0]:04d}',
        email=f'jane{_cnt[0]}@test.com'
    )


def make_property(owner):
    _cnt[0] += 1
    from properties.models import Property
    return Property.objects.create(
        title=f'Test Villa {_cnt[0]}', slug=f'test-villa-{_cnt[0]}',
        property_type='apartment', listing_type='rent', status='available',
        price=2500, address='123 Test St', city='Machakos', country='Kenya',
        owner=owner, bedrooms=1, bathrooms=1, area=30
    )


def make_booking(managed_by, guest=None, prop=None):
    if guest is None:
        guest = make_guest()
    if prop is None:
        prop = make_property(managed_by)
    today = timezone.now().date()
    return Booking.objects.create(
        asset_property=prop, guest=guest, managed_by=managed_by,
        check_in_date=today + datetime.timedelta(days=2),
        check_out_date=today + datetime.timedelta(days=5),
        room_rate=Decimal('2500.00'),
        num_adults=2, source='direct',
    )


class BookingModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.booking = make_booking(self.user)

    def test_booking_reference_auto_generated(self):
        """Booking reference is auto-generated in BK-YYYY-NNNN format."""
        self.assertTrue(self.booking.booking_reference.startswith('BK-'))
        self.assertIsNotNone(self.booking.booking_reference)

    def test_booking_reference_unique(self):
        """Two bookings get different references."""
        b2 = make_booking(self.user)
        self.assertNotEqual(self.booking.booking_reference, b2.booking_reference)

    def test_total_nights_computed(self):
        """total_nights = checkout - checkin."""
        self.assertEqual(self.booking.total_nights, 3)

    def test_subtotal_computed(self):
        """subtotal = room_rate * total_nights."""
        self.assertEqual(self.booking.subtotal, Decimal('7500.00'))

    def test_total_amount_computed(self):
        """total_amount = subtotal + fees - discounts."""
        self.booking.cleaning_fee = Decimal('250.00')
        self.booking.save()
        self.assertEqual(self.booking.total_amount, Decimal('7750.00'))

    def test_balance_due_no_payments(self):
        """balance_due equals total_amount when no payments."""
        self.assertEqual(self.booking.balance_due, self.booking.total_amount)

    def test_balance_due_after_payment(self):
        """balance_due decreases after payment recorded."""
        BookingPayment.objects.create(
            booking=self.booking, payment_method='cash',
            amount=Decimal('2500.00'), status='completed',
            paid_at=timezone.now(), recorded_by=self.user
        )
        self.assertEqual(self.booking.balance_due, self.booking.total_amount - Decimal('2500.00'))

    def test_is_upcoming_true(self):
        """is_upcoming is True for future confirmed booking."""
        self.booking.status = 'confirmed'
        self.booking.save()
        self.assertTrue(self.booking.is_upcoming)

    def test_is_upcoming_false_for_past(self):
        """is_upcoming is False for past booking."""
        today = timezone.now().date()
        self.booking.check_in_date = today - datetime.timedelta(days=5)
        self.booking.check_out_date = today - datetime.timedelta(days=2)
        self.booking.save()
        self.assertFalse(self.booking.is_upcoming)

    def test_status_default_pending(self):
        """Default status is pending."""
        self.assertEqual(self.booking.status, 'pending')

    def test_str_representation(self):
        """__str__ includes reference and guest."""
        s = str(self.booking)
        self.assertIn('BK-', s)
        self.assertIn('Doe', s)

    def test_get_status_badge_class(self):
        """Badge class maps correctly for each status."""
        self.booking.status = 'confirmed'
        self.assertEqual(self.booking.get_status_badge_class(), 'primary')
        self.booking.status = 'checked_in'
        self.assertEqual(self.booking.get_status_badge_class(), 'success')
        self.booking.status = 'cancelled'
        self.assertEqual(self.booking.get_status_badge_class(), 'danger')

    def test_nights_until_checkin(self):
        """nights_until_checkin returns positive days for future checkin."""
        self.assertGreaterEqual(self.booking.nights_until_checkin, 1)

    def test_message_creation(self):
        """Messages can be created for a booking."""
        msg = BookingMessage.objects.create(
            booking=self.booking, direction='outbound', channel='whatsapp',
            sender_name='System', content='Confirmation message'
        )
        self.assertEqual(self.booking.messages.count(), 1)
        self.assertEqual(msg.channel, 'whatsapp')

    def test_note_creation(self):
        """Notes can be added to a booking."""
        note = BookingNote.objects.create(
            booking=self.booking, author=self.user,
            note='Internal note', is_private=True
        )
        self.assertEqual(self.booking.notes.count(), 1)
        self.assertTrue(note.is_private)

    def test_payment_model_str(self):
        """BookingPayment __str__ includes amount and method."""
        pay = BookingPayment.objects.create(
            booking=self.booking, payment_method='mpesa',
            amount=Decimal('1000.00'), status='completed',
            paid_at=timezone.now(), recorded_by=self.user
        )
        s = str(pay)
        self.assertIn('1000', s)
        self.assertIn('mpesa', s)


class BookingFormTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.guest = make_guest()
        self.prop = make_property(self.user)
        self.today = timezone.now().date()

    def test_booking_form_valid_data(self):
        """BookingForm is valid with correct data."""
        from bookings.forms import BookingForm
        form = BookingForm(data={
            'asset_property' : self.prop.pk,
            'guest': self.guest.pk,
            'check_in_date': self.today + datetime.timedelta(days=3),
            'check_out_date': self.today + datetime.timedelta(days=6),
            'room_rate': '2500',
            'num_adults': 2,
            'num_children': 0,
            'source': 'direct',
            'cleaning_fee': '0',
            'service_fee': '0',
            'tax_amount': '0',
            'discount_amount': '0',
            'deposit_amount': '0',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_booking_form_checkout_before_checkin_invalid(self):
        """BookingForm is invalid if checkout is before checkin."""
        from bookings.forms import BookingForm
        form = BookingForm(data={
            'asset_property' : self.prop.pk,
            'guest': self.guest.pk,
            'check_in_date': self.today + datetime.timedelta(days=5),
            'check_out_date': self.today + datetime.timedelta(days=3),
            'room_rate': '2500',
            'num_adults': 1, 'num_children': 0, 'source': 'direct',
            'cleaning_fee': '0', 'service_fee': '0',
            'tax_amount': '0', 'discount_amount': '0', 'deposit_amount': '0',
        })
        self.assertFalse(form.is_valid())

    def test_payment_form_valid(self):
        """PaymentForm is valid with positive amount."""
        from bookings.forms import PaymentForm
        form = PaymentForm(data={
            'payment_method': 'mpesa',
            'amount': '2500',
            'paid_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_payment_form_negative_amount_invalid(self):
        """PaymentForm rejects zero or negative amounts."""
        from bookings.forms import PaymentForm
        form = PaymentForm(data={
            'payment_method': 'cash', 'amount': '-100',
            'paid_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertFalse(form.is_valid())


class BookingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.booking = make_booking(self.user)
        self.client.force_login(self.user)

    def test_booking_list_requires_login(self):
        """Unauthenticated users are redirected."""
        self.client.logout()
        resp = self.client.get(reverse('bookings:list'))
        self.assertNotEqual(resp.status_code, 200)

    def test_booking_list_view_200(self):
        """Logged-in user can see booking list."""
        resp = self.client.get(reverse('bookings:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.booking.booking_reference)

    def test_booking_list_only_shows_own_bookings(self):
        """List view only shows bookings managed by the current user."""
        other_user = make_user('other@test.com')
        other_booking = make_booking(other_user)
        resp = self.client.get(reverse('bookings:list'))
        self.assertNotContains(resp, other_booking.booking_reference)

    def test_booking_detail_200(self):
        """Detail view returns 200 for the booking."""
        resp = self.client.get(reverse('bookings:detail', kwargs={'pk': self.booking.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_booking_create_get(self):
        """Create view GET returns 200."""
        resp = self.client.get(reverse('bookings:create'))
        self.assertEqual(resp.status_code, 200)

    def test_check_in_view_updates_status(self):
        """POST to check-in view changes status to checked_in."""
        self.booking.status = 'confirmed'
        self.booking.save()
        resp = self.client.post(reverse('bookings:check_in', kwargs={'pk': self.booking.pk}), {
            'check_in_time': '14:00', 'internal_notes': ''
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'checked_in')

    def test_check_out_view_updates_status(self):
        """POST to checkout view changes status to checked_out."""
        self.booking.status = 'checked_in'
        self.booking.save()
        resp = self.client.post(reverse('bookings:check_out', kwargs={'pk': self.booking.pk}), {
            'check_out_time': '11:00'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'checked_out')

    def test_check_out_creates_cleaning_task(self):
        """Checkout creates a cleaning task automatically."""
        from housekeeping.models import CleaningTask
        self.booking.status = 'checked_in'
        self.booking.save()
        initial_count = CleaningTask.objects.count()
        self.client.post(reverse('bookings:check_out', kwargs={'pk': self.booking.pk}), {
            'check_out_time': '11:00'
        })
        self.assertEqual(CleaningTask.objects.count(), initial_count + 1)

    def test_record_payment_creates_cashbook_entry(self):
        """Recording a payment also creates a cashbook entry."""
        from financials.models import CashbookEntry
        initial = CashbookEntry.objects.count()
        self.client.post(reverse('bookings:record_payment', kwargs={'pk': self.booking.pk}), {
            'payment_method': 'cash',
            'amount': '2500',
            'paid_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertGreater(CashbookEntry.objects.count(), initial)

    def test_cancel_booking(self):
        """Cancelling a booking changes status to cancelled."""
        resp = self.client.post(reverse('bookings:cancel', kwargs={'pk': self.booking.pk}), {
            'reason': 'Guest cancelled'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_booking_calendar_view(self):
        """Calendar view returns 200."""
        resp = self.client.get(reverse('bookings:calendar'))
        self.assertEqual(resp.status_code, 200)

    def test_calendar_events_api(self):
        """Calendar events API returns JSON list."""
        resp = self.client.get(reverse('bookings:calendar_events'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
