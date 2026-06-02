import logging
import requests

logger = logging.getLogger(__name__)


class AirbnbClient:
    BASE_URL = 'https://api.airbnb.com/v2'

    def __init__(self, access_token=None, listing_id=None):
        self.access_token = access_token
        self.listing_id = listing_id
        self.mock_mode = not access_token

    def _headers(self):
        return {'X-Airbnb-OAuth-Token': self.access_token, 'Content-Type': 'application/json'}

    def _get(self, endpoint, params=None):
        if self.mock_mode:
            logger.info(f'[MOCK Airbnb] GET {endpoint}')
            return {}
        resp = requests.get(f'{self.BASE_URL}/{endpoint}', headers=self._headers(), params=params or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint, data=None):
        if self.mock_mode:
            logger.info(f'[MOCK Airbnb] POST {endpoint}')
            return {}
        resp = requests.post(f'{self.BASE_URL}/{endpoint}', headers=self._headers(), json=data or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_reservations(self):
        return self._get('reservations', {'listing_id': self.listing_id})

    def get_reservation(self, reservation_id):
        return self._get(f'reservations/{reservation_id}')

    def send_message_to_guest(self, thread_id, message):
        return self._post(f'messages', {'thread_id': thread_id, 'message': message})

    def get_guest_messages(self, thread_id):
        return self._get(f'messages', {'thread_id': thread_id})

    def update_availability(self, dates, available):
        return self._post('availability', {'listing_id': self.listing_id, 'dates': dates, 'available': available})

    def get_reviews(self):
        return self._get('reviews', {'listing_id': self.listing_id})

    def reply_to_review(self, review_id, response_text):
        return self._post(f'reviews/{review_id}/response', {'response': response_text})
