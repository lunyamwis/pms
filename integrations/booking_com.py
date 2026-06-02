import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BookingComClient:
    BASE_URL = 'https://partner.api.booking.com/v1'

    def __init__(self, username=None, password=None, hotel_id=None):
        self.username = username or settings.BOOKING_COM_USERNAME
        self.password = password or settings.BOOKING_COM_PASSWORD
        self.hotel_id = hotel_id
        self.mock_mode = not (self.username and self.password)

    def _get(self, endpoint, params=None):
        if self.mock_mode:
            logger.info(f'[MOCK Booking.com] GET {endpoint} params={params}')
            return {}
        url = f'{self.BASE_URL}/{endpoint}'
        resp = requests.get(url, auth=(self.username, self.password), params=params or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint, data=None):
        if self.mock_mode:
            logger.info(f'[MOCK Booking.com] POST {endpoint} data={data}')
            return {'success': True}
        url = f'{self.BASE_URL}/{endpoint}'
        resp = requests.post(url, auth=(self.username, self.password), json=data or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_reservations(self, from_date, to_date):
        return self._get(f'hotels/{self.hotel_id}/reservations', {
            'check_in': str(from_date), 'check_out': str(to_date)
        })

    def get_reservation(self, reservation_id):
        return self._get(f'hotels/{self.hotel_id}/reservations/{reservation_id}')

    def confirm_reservation(self, reservation_id):
        return self._post(f'hotels/{self.hotel_id}/reservations/{reservation_id}/confirm')

    def cancel_reservation(self, reservation_id, reason=''):
        return self._post(f'hotels/{self.hotel_id}/reservations/{reservation_id}/cancel', {'reason': reason})

    def send_message_to_guest(self, reservation_id, message):
        return self._post(f'hotels/{self.hotel_id}/reservations/{reservation_id}/messages', {'message': message})

    def get_guest_messages(self, reservation_id):
        return self._get(f'hotels/{self.hotel_id}/reservations/{reservation_id}/messages')

    def close_dates(self, room_type_id, from_date, to_date):
        return self._post(f'hotels/{self.hotel_id}/availabilities', {
            'room_type_id': room_type_id, 'from': str(from_date),
            'to': str(to_date), 'available': 0
        })

    def get_property_reviews(self):
        return self._get(f'hotels/{self.hotel_id}/reviews')

    def reply_to_review(self, review_id, reply):
        return self._post(f'hotels/{self.hotel_id}/reviews/{review_id}/reply', {'reply': reply})
