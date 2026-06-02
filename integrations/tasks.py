import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_booking_confirmation(self, booking_id):
    from bookings.models import Booking, BookingMessage
    from integrations.whatsapp import WhatsAppService
    from integrations.models import IntegrationLog
    try:
        booking = Booking.objects.select_related('guest', 'booking_property').get(pk=booking_id)
        svc = WhatsAppService()
        phone = booking.guest.contact_number
        message = svc.format_booking_confirmation(booking)
        channel = 'whatsapp'
        try:
            svc.send_message(phone, message)
        except Exception:
            # Fallback to email
            channel = 'email'
            _send_email_message(booking, 'booking_confirmation', message)
        booking.confirmation_sent = True
        booking.save(update_fields=['confirmation_sent'])
        BookingMessage.objects.create(
            booking=booking, direction='outbound', channel=channel,
            sender_name='System', content=message, status='sent'
        )
        IntegrationLog.objects.create(
            platform=channel, action='send_message', status='success', booking=booking
        )
    except Exception as exc:
        logger.error(f'send_booking_confirmation failed for booking {booking_id}: {exc}')
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_pre_arrival_messages(self):
    from bookings.models import Booking
    from integrations.whatsapp import WhatsAppService
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    bookings = Booking.objects.filter(
        check_in_date=tomorrow,
        status='confirmed',
        pre_arrival_sent=False,
    ).select_related('guest', 'booking_property')
    svc = WhatsAppService()
    for booking in bookings:
        try:
            message = svc.format_pre_arrival(booking)
            try:
                svc.send_message(booking.guest.contact_number, message)
                channel = 'whatsapp'
            except Exception:
                _send_email_message(booking, 'pre_arrival', message)
                channel = 'email'
            booking.pre_arrival_sent = True
            booking.save(update_fields=['pre_arrival_sent'])
            from bookings.models import BookingMessage
            BookingMessage.objects.create(
                booking=booking, direction='outbound', channel=channel,
                sender_name='System', content=message, status='sent'
            )
        except Exception as e:
            logger.error(f'Pre-arrival message failed for booking {booking.pk}: {e}')


@shared_task(bind=True, max_retries=3)
def send_checkout_reminders(self):
    from bookings.models import Booking
    from integrations.whatsapp import WhatsAppService
    today = timezone.now().date()
    bookings = Booking.objects.filter(
        check_out_date=today, status='checked_in'
    ).select_related('guest', 'booking_property')
    svc = WhatsAppService()
    for booking in bookings:
        try:
            message = svc.format_checkout_reminder(booking)
            try:
                svc.send_message(booking.guest.contact_number, message)
            except Exception:
                _send_email_message(booking, 'checkout_reminder', message)
        except Exception as e:
            logger.error(f'Checkout reminder failed for booking {booking.pk}: {e}')


@shared_task(bind=True, max_retries=3)
def send_review_request(self, booking_id):
    from bookings.models import Booking, BookingMessage
    from integrations.whatsapp import WhatsAppService
    try:
        booking = Booking.objects.select_related('guest', 'booking_property').get(pk=booking_id)
        if booking.review_request_sent:
            return
        svc = WhatsAppService()
        message = svc.format_review_request(booking)
        channel = 'whatsapp'
        try:
            svc.send_message(booking.guest.contact_number, message)
        except Exception:
            channel = 'email'
            _send_email_message(booking, 'review_request', message)
        booking.review_request_sent = True
        booking.save(update_fields=['review_request_sent'])
        BookingMessage.objects.create(
            booking=booking, direction='outbound', channel=channel,
            sender_name='System', content=message, status='sent'
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def send_pending_review_requests(self):
    from bookings.models import Booking
    from django.utils import timezone
    two_hours_ago = timezone.now() - timezone.timedelta(hours=2)
    bookings = Booking.objects.filter(
        status='checked_out',
        review_request_sent=False,
        updated_at__lte=two_hours_ago,
    )
    for booking in bookings:
        send_review_request.delay(booking.pk)


@shared_task
def send_receipt(booking_id):
    from bookings.models import Booking
    from financials.models import Receipt
    from integrations.whatsapp import WhatsAppService
    try:
        booking = Booking.objects.select_related('guest', 'booking_property').get(pk=booking_id)
        receipt = Receipt.objects.filter(booking=booking).first()
        if not receipt:
            return
        svc = WhatsAppService()
        msg = f"Dear {booking.guest.full_name},\n\nPlease find your receipt for your stay at {booking.property.title}.\n\nReceipt No: {receipt.receipt_number}\nTotal: KSh {receipt.total_amount:,.2f}\n\nThank you!"
        try:
            svc.send_message(booking.guest.contact_number, msg)
            receipt.sent_via_whatsapp = True
        except Exception:
            _send_email_message(booking, 'receipt', msg)
            receipt.sent_via_email = True
        receipt.save()
        booking.receipt_sent = True
        booking.save(update_fields=['receipt_sent'])
    except Exception as e:
        logger.error(f'send_receipt failed: {e}')


@shared_task
def send_receipt_task(booking_id, channel='both'):
    send_receipt(booking_id)


@shared_task
def send_custom_message(booking_id, content, channel='whatsapp'):
    from bookings.models import Booking
    from integrations.whatsapp import WhatsAppService
    try:
        booking = Booking.objects.select_related('guest', 'booking_property').get(pk=booking_id)
        if channel in ('whatsapp', 'both'):
            svc = WhatsAppService()
            try:
                svc.send_message(booking.guest.contact_number, content)
            except Exception:
                _send_email_message(booking, 'general', content)
        if channel == 'email':
            _send_email_message(booking, 'general', content)
    except Exception as e:
        logger.error(f'send_custom_message failed: {e}')


@shared_task
def sync_all_booking_com():
    from integrations.models import BookingComProperty
    from integrations.booking_com import BookingComClient
    for config in BookingComProperty.objects.filter(is_connected=True, sync_enabled=True):
        try:
            client = BookingComClient(config.username, config.password, config.hotel_id)
            from django.utils import timezone
            today = timezone.now().date()
            future = today + timezone.timedelta(days=90)
            reservations = client.get_reservations(today, future)
            logger.info(f'Synced Booking.com for property {config.property}: {reservations}')
        except Exception as e:
            logger.error(f'Booking.com sync failed: {e}')


@shared_task
def sync_all_airbnb():
    from integrations.models import AirbnbProperty
    from integrations.airbnb import AirbnbClient
    for config in AirbnbProperty.objects.filter(is_connected=True, sync_enabled=True):
        try:
            client = AirbnbClient(config.access_token, config.listing_id)
            reservations = client.get_reservations()
            logger.info(f'Synced Airbnb for property {config.property}: {reservations}')
        except Exception as e:
            logger.error(f'Airbnb sync failed: {e}')


def _send_email_message(booking, template_type, message):
    from django.core.mail import send_mail
    from django.conf import settings
    if not booking.guest.email:
        return
    try:
        send_mail(
            subject=f'Message from {booking.property.title}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.guest.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f'Email fallback failed: {e}')
