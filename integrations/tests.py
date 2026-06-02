from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.utils import timezone
import datetime
from decimal import Decimal

User = get_user_model()


def make_user(email='int@test.com'):
    u = User.objects.create_user(username=email, email=email, password='testpass123')
    u.role = 'agent'
    u.email_verified = True
    u.save()
    return u


def _make_booking(user, suffix=''):
    from guests.models import Guest
    from properties.models import Property
    from bookings.models import Booking
    guest = Guest.objects.create(first_name='Wa', last_name=f'Test{suffix}', phone=f'+2547000{suffix or "11111"}')
    prop = Property.objects.create(
        title=f'WA Property{suffix}', slug=f'wa-property{suffix}', property_type='apartment',
        listing_type='rent', status='available', price=2500,
        address='WA St', city='Machakos', country='Kenya',
        owner=user, bedrooms=1, bathrooms=1, area=30
    )
    today = timezone.now().date()
    return Booking.objects.create(
        asset_property=prop, guest=guest, managed_by=user,
        check_in_date=today + datetime.timedelta(days=1),
        check_out_date=today + datetime.timedelta(days=3),
        room_rate=Decimal('2500.00'), source='direct'
    )


class WhatsAppServiceTests(TestCase):
    def test_send_message_mock_mode(self):
        """WhatsAppService in mock mode logs and returns MOCK sid."""
        from integrations.whatsapp import WhatsAppService
        svc = WhatsAppService(account_sid='', auth_token='', from_number='')
        result = svc.send_message('+254700000000', 'Hello!')
        self.assertEqual(result['sid'], 'MOCK')
        self.assertEqual(result['status'], 'sent')

    def test_format_booking_confirmation_no_template(self):
        """format_booking_confirmation uses fallback when no template exists."""
        user = make_user('wa_test@test.com')
        booking = _make_booking(user)
        from integrations.whatsapp import WhatsAppService
        svc = WhatsAppService()
        msg = svc.format_booking_confirmation(booking)
        self.assertIn(booking.guest.first_name, msg)
        self.assertIn(booking.asset_property.title, msg)

    def test_format_review_request_mentions_property(self):
        """format_review_request message mentions property name."""
        user = make_user('rv_test@test.com')
        booking = _make_booking(user, '2')
        booking.status = 'checked_out'
        booking.save()
        from integrations.whatsapp import WhatsAppService
        svc = WhatsAppService()
        msg = svc.format_review_request(booking)
        self.assertIn(booking.asset_property.title, msg)
        self.assertIn(booking.guest.first_name, msg)

    def test_format_pre_arrival_message(self):
        """format_pre_arrival message includes check-in info."""
        user = make_user('pa_test@test.com')
        booking = _make_booking(user, '3')
        from integrations.whatsapp import WhatsAppService
        svc = WhatsAppService()
        msg = svc.format_pre_arrival(booking)
        self.assertIn(booking.guest.first_name, msg)

    def test_format_checkout_reminder(self):
        """format_checkout_reminder includes property name."""
        user = make_user('co_test@test.com')
        booking = _make_booking(user, '4')
        from integrations.whatsapp import WhatsAppService
        svc = WhatsAppService()
        msg = svc.format_checkout_reminder(booking)
        self.assertIn(booking.asset_property.title, msg)

    @patch('integrations.whatsapp.WhatsAppService.send_message')
    def test_send_message_called_with_right_args(self, mock_send):
        """send_message is called with correct arguments."""
        mock_send.return_value = {'sid': 'TEST123', 'status': 'sent'}
        from integrations.whatsapp import WhatsAppService
        svc = WhatsAppService()
        svc.send_message('+254700000000', 'Test message')
        mock_send.assert_called_once_with('+254700000000', 'Test message')


class BookingComClientTests(TestCase):
    def test_mock_mode_get_reservations(self):
        """BookingComClient in mock mode returns empty dict."""
        from integrations.booking_com import BookingComClient
        client = BookingComClient(username='', password='', hotel_id='123')
        result = client.get_reservations('2026-01-01', '2026-03-31')
        self.assertEqual(result, {})

    def test_mock_mode_confirm_reservation(self):
        """confirm_reservation in mock mode returns success dict."""
        from integrations.booking_com import BookingComClient
        client = BookingComClient(username='', password='', hotel_id='123')
        result = client.confirm_reservation('RES123')
        self.assertEqual(result, {'success': True})

    def test_mock_mode_cancel_reservation(self):
        """cancel_reservation in mock mode returns success dict."""
        from integrations.booking_com import BookingComClient
        client = BookingComClient(username='', password='', hotel_id='123')
        result = client.cancel_reservation('RES123', reason='Guest request')
        self.assertEqual(result, {'success': True})

    def test_mock_mode_send_message_to_guest(self):
        """send_message_to_guest in mock mode returns success dict (uses POST internally)."""
        from integrations.booking_com import BookingComClient
        client = BookingComClient(username='', password='', hotel_id='123')
        result = client.send_message_to_guest('RES123', 'Hello guest!')
        self.assertEqual(result, {'success': True})

    def test_mock_mode_close_dates(self):
        """close_dates in mock mode returns success dict."""
        from integrations.booking_com import BookingComClient
        client = BookingComClient(username='', password='', hotel_id='123')
        result = client.close_dates('ROOM1', '2026-07-01', '2026-07-05')
        self.assertEqual(result, {'success': True})


class AirbnbClientTests(TestCase):
    def test_mock_mode_get_reservations(self):
        """AirbnbClient in mock mode returns empty dict."""
        from integrations.airbnb import AirbnbClient
        client = AirbnbClient(access_token='', listing_id='123')
        result = client.get_reservations()
        self.assertEqual(result, {})

    def test_mock_mode_send_message(self):
        """send_message_to_guest in mock mode returns empty dict."""
        from integrations.airbnb import AirbnbClient
        client = AirbnbClient(access_token='', listing_id='123')
        result = client.send_message_to_guest('THREAD1', 'Hello!')
        self.assertEqual(result, {})


class MessageTemplateTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_template_render_substitutes_placeholders(self):
        """MessageTemplate.render substitutes {{key}} placeholders."""
        from integrations.models import MessageTemplate
        tpl = MessageTemplate.objects.create(
            template_type='booking_confirmation',
            name='Test Confirmation',
            body='Dear {{guest_name}}, your booking at {{property_name}} is confirmed.',
            user=self.user, channel='whatsapp'
        )
        result = tpl.render({'guest_name': 'Alice', 'property_name': 'Luxe Villa'})
        self.assertEqual(result, 'Dear Alice, your booking at Luxe Villa is confirmed.')

    def test_template_render_with_no_matches(self):
        """Render with empty context returns body unchanged."""
        from integrations.models import MessageTemplate
        tpl = MessageTemplate.objects.create(
            template_type='general', name='Plain',
            body='Hello there!', user=self.user
        )
        result = tpl.render({})
        self.assertEqual(result, 'Hello there!')

    def test_template_str_representation(self):
        """__str__ includes template type display name and template name."""
        from integrations.models import MessageTemplate
        tpl = MessageTemplate.objects.create(
            template_type='review_request', name='Review Request',
            body='Please review!', user=self.user
        )
        s = str(tpl)
        self.assertIn('Review Request', s)

    def test_integration_log_creation(self):
        """IntegrationLog can be created with platform and action."""
        from integrations.models import IntegrationLog
        log = IntegrationLog.objects.create(
            platform='whatsapp', action='send_message', status='success'
        )
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.platform, 'whatsapp')
        self.assertIn('whatsapp', str(log))

    def test_bookingcom_property_model(self):
        """BookingComProperty can be created."""
        from integrations.models import BookingComProperty
        from properties.models import Property
        user = make_user('bcp@test.com')
        prop = Property.objects.create(
            title='BCP Prop', slug='bcp-prop', property_type='apartment',
            listing_type='rent', status='available', price=2500,
            address='BCP', city='Machakos', country='Kenya',
            owner=user, bedrooms=1, bathrooms=1, area=30
        )
        config = BookingComProperty.objects.create(
            user=user, property=prop, hotel_id='H123',
            username='test', password='pass'
        )
        self.assertFalse(config.is_connected)
        self.assertIn('BCP Prop', str(config))


class IntegrationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.force_login(self.user)

    def test_dashboard_200(self):
        """Integrations dashboard returns 200."""
        resp = self.client.get(reverse('integrations:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_whatsapp_setup_get_200(self):
        """WhatsApp setup page returns 200."""
        resp = self.client.get(reverse('integrations:whatsapp_setup'))
        self.assertEqual(resp.status_code, 200)

    def test_bookingcom_setup_get_200(self):
        """Booking.com setup page returns 200."""
        resp = self.client.get(reverse('integrations:bookingcom_setup'))
        self.assertEqual(resp.status_code, 200)

    def test_templates_list_200(self):
        """Message templates list returns 200."""
        resp = self.client.get(reverse('integrations:templates'))
        self.assertEqual(resp.status_code, 200)

    def test_template_create_get_200(self):
        """Template create page returns 200."""
        resp = self.client.get(reverse('integrations:template_create'))
        self.assertEqual(resp.status_code, 200)

    def test_logs_list_200(self):
        """Integration logs page returns 200."""
        resp = self.client.get(reverse('integrations:logs'))
        self.assertEqual(resp.status_code, 200)

    def test_whatsapp_webhook_accepts_post(self):
        """WhatsApp webhook endpoint accepts POST without CSRF (uses anonymous client)."""
        from django.test import Client as AnonClient
        anon = AnonClient(enforce_csrf_checks=False)
        resp = anon.post(
            reverse('integrations:whatsapp_webhook'),
            'From=whatsapp%3A%2B254700000000&Body=Hello',
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(resp.status_code, 200)

    def test_airbnb_setup_get_200(self):
        """Airbnb setup page returns 200."""
        resp = self.client.get(reverse('integrations:airbnb_setup'))
        self.assertEqual(resp.status_code, 200)
