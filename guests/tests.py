from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from guests.models import Guest, GuestDocument, GuestReview

User = get_user_model()


def make_user(email='mgr@test.com', password='testpass123'):
    u = User.objects.create_user(username=email, email=email, password=password, first_name='Test', last_name='Mgr')
    u.role = 'agent'
    u.email_verified = True
    u.save()
    return u


def make_guest(**kwargs):
    defaults = {'first_name': 'Alice', 'last_name': 'Smith', 'phone': '+254712345678', 'email': 'alice@test.com'}
    defaults.update(kwargs)
    return Guest.objects.create(**defaults)


class GuestModelTests(TestCase):
    def setUp(self):
        self.guest = make_guest()

    def test_full_name(self):
        """full_name property combines first and last name."""
        self.assertEqual(self.guest.full_name, 'Alice Smith')

    def test_total_bookings_zero(self):
        """New guest has zero bookings."""
        self.assertEqual(self.guest.total_bookings, 0)

    def test_is_repeat_guest_false(self):
        """Guest with no completed stays is not a repeat guest."""
        self.assertFalse(self.guest.is_repeat_guest)

    def test_total_spent_zero(self):
        """New guest has zero total spent."""
        self.assertEqual(self.guest.total_spent, 0)

    def test_blacklist_guest(self):
        """Can blacklist a guest with a reason."""
        self.guest.is_blacklisted = True
        self.guest.blacklist_reason = 'Property damage'
        self.guest.save()
        self.guest.refresh_from_db()
        self.assertTrue(self.guest.is_blacklisted)
        self.assertEqual(self.guest.blacklist_reason, 'Property damage')

    def test_vip_flag(self):
        """Can mark a guest as VIP."""
        self.guest.is_vip = True
        self.guest.save()
        self.guest.refresh_from_db()
        self.assertTrue(self.guest.is_vip)

    def test_str_representation(self):
        """__str__ returns full name."""
        self.assertEqual(str(self.guest), 'Alice Smith')

    def test_contact_number_prefers_whatsapp(self):
        """contact_number returns WhatsApp if set, else phone."""
        self.guest.whatsapp_number = '+254799999999'
        self.guest.save()
        self.assertEqual(self.guest.contact_number, '+254799999999')

    def test_contact_number_fallback_phone(self):
        """contact_number returns phone when no WhatsApp."""
        self.assertEqual(self.guest.contact_number, '+254712345678')

    def test_last_stay_none_for_new_guest(self):
        """last_stay is None for guest with no bookings."""
        self.assertIsNone(self.guest.last_stay)

    def test_get_absolute_url(self):
        """get_absolute_url returns valid URL."""
        url = self.guest.get_absolute_url()
        self.assertIn(str(self.guest.pk), url)


class GuestFormTests(TestCase):
    def test_guest_form_valid(self):
        """GuestForm is valid with required fields."""
        from guests.forms import GuestForm
        form = GuestForm(data={'first_name': 'Bob', 'last_name': 'Jones', 'phone': '+254700000001', 'language_preference': 'en'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_guest_form_missing_phone_invalid(self):
        """GuestForm requires phone."""
        from guests.forms import GuestForm
        form = GuestForm(data={'first_name': 'Bob', 'last_name': 'Jones'})
        self.assertFalse(form.is_valid())

    def test_search_form_blank_is_valid(self):
        """GuestSearchForm with no input is still valid."""
        from guests.forms import GuestSearchForm
        form = GuestSearchForm(data={})
        self.assertTrue(form.is_valid())


class GuestViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)
        self.guest = make_guest()

    def test_guest_list_200(self):
        resp = self.client.get(reverse('guests:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Alice Smith')

    def test_guest_detail_200(self):
        resp = self.client.get(reverse('guests:detail', kwargs={'pk': self.guest.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_guest_create_get(self):
        resp = self.client.get(reverse('guests:create'))
        self.assertEqual(resp.status_code, 200)

    def test_guest_create_post(self):
        count_before = Guest.objects.count()
        resp = self.client.post(reverse('guests:create'), {
            'first_name': 'New', 'last_name': 'Guest',
            'phone': '+254711111111', 'language_preference': 'en'
        })
        self.assertEqual(Guest.objects.count(), count_before + 1)

    def test_guest_blacklist_toggle(self):
        """Blacklist view toggles is_blacklisted."""
        self.client.post(reverse('guests:blacklist', kwargs={'pk': self.guest.pk}), {'reason': 'Test'})
        self.guest.refresh_from_db()
        self.assertTrue(self.guest.is_blacklisted)
        # Toggle again
        self.client.post(reverse('guests:blacklist', kwargs={'pk': self.guest.pk}), {})
        self.guest.refresh_from_db()
        self.assertFalse(self.guest.is_blacklisted)

    def test_guest_export_csv(self):
        resp = self.client.get(reverse('guests:export'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')

    def test_guest_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('guests:list'))
        self.assertNotEqual(resp.status_code, 200)
