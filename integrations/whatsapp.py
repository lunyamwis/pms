import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_number = from_number or settings.TWILIO_WHATSAPP_FROM
        self._client = None

    @property
    def client(self):
        if not self._client and self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.warning('Twilio not installed. WhatsApp messages will be logged only.')
        return self._client

    def send_message(self, to_number: str, message: str) -> dict:
        to_wa = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number
        if not self.client:
            logger.info(f'[MOCK WhatsApp] To: {to_wa}\nMessage: {message}')
            return {'sid': 'MOCK', 'status': 'sent'}
        try:
            msg = self.client.messages.create(
                from_=self.from_number,
                to=to_wa,
                body=message,
            )
            logger.info(f'WhatsApp sent: {msg.sid} to {to_wa}')
            return {'sid': msg.sid, 'status': msg.status}
        except Exception as e:
            logger.error(f'WhatsApp send failed: {e}')
            raise

    def send_document(self, to_number: str, document_url: str, caption: str = '') -> dict:
        to_wa = f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number
        if not self.client:
            logger.info(f'[MOCK WhatsApp Doc] To: {to_wa}, URL: {document_url}')
            return {'sid': 'MOCK', 'status': 'sent'}
        try:
            msg = self.client.messages.create(
                from_=self.from_number,
                to=to_wa,
                media_url=[document_url],
                body=caption,
            )
            return {'sid': msg.sid, 'status': msg.status}
        except Exception as e:
            logger.error(f'WhatsApp document send failed: {e}')
            raise

    def format_booking_confirmation(self, booking) -> str:
        from integrations.models import MessageTemplate
        tpl = MessageTemplate.objects.filter(
            template_type='booking_confirmation', is_active=True
        ).first()
        if tpl:
            return tpl.render({
                'guest_name': booking.guest.full_name,
                'booking_reference': booking.booking_reference,
                'property_name': booking.asset_property.title,
                'check_in_date': booking.check_in_date.strftime('%d %b %Y'),
                'check_out_date': booking.check_out_date.strftime('%d %b %Y'),
                'total_nights': booking.total_nights,
                'total_amount': f'{booking.total_amount:,.2f}',
                'room_rate': f'{booking.room_rate:,.2f}',
                'num_guests': booking.num_guests,
            })
        return (
            f"Dear {booking.guest.full_name},\n\n"
            f"Your booking at {booking.asset_property.title} is confirmed!\n\n"
            f"Reference: {booking.booking_reference}\n"
            f"Check-in: {booking.check_in_date.strftime('%d %b %Y')}\n"
            f"Check-out: {booking.check_out_date.strftime('%d %b %Y')}\n"
            f"Nights: {booking.total_nights}\n"
            f"Total: KSh {booking.total_amount:,.2f}\n\n"
            f"We look forward to hosting you!\n\nWarm regards,\n{booking.asset_property.title}"
        )

    def format_pre_arrival(self, booking) -> str:
        prop = booking.asset_property
        return (
            f"Hello {booking.guest.full_name}! 👋\n\n"
            f"Your stay at {prop.title} starts tomorrow ({booking.check_in_date.strftime('%d %b')}).\n\n"
            f"Check-in: After {prop.check_in_time or '2:00 PM'}\n"
            f"Access: {prop.access_instructions or 'We will share details shortly'}\n"
            f"WiFi: {prop.wifi_name or 'Available'} / {prop.wifi_password or ''}\n\n"
            f"If you have any questions, reply to this message.\n\nSee you soon! 🏠"
        )

    def format_review_request(self, booking) -> str:
        return (
            f"Dear {booking.guest.full_name},\n\n"
            f"Thank you for staying at {booking.asset_property.title}! 🌟\n\n"
            f"We hope you had a wonderful experience. "
            f"Would you mind leaving us a review? It really helps us improve and helps "
            f"other travelers find great accommodation.\n\n"
            f"Your feedback means the world to us!\n\nWarm regards,\n{booking.asset_property.title}"
        )

    def format_checkout_reminder(self, booking) -> str:
        return (
            f"Good morning {booking.guest.full_name}! ☀️\n\n"
            f"This is a friendly reminder that today is your checkout day.\n"
            f"Check-out time: By {booking.asset_property.check_out_time or '11:00 AM'}\n\n"
            f"Please ensure you leave the key/access card at the designated spot.\n\n"
            f"Thank you for choosing {booking.asset_property.title}! 🙏"
        )
