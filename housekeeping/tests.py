from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from housekeeping.models import CleaningTask, MaintenanceRequest, HousekeepingStaff, RoomServiceOrder

User = get_user_model()


_counter = [0]


def make_user(email=None):
    _counter[0] += 1
    email = email or f'hk{_counter[0]}@test.com'
    u = User.objects.create_user(username=email, email=email, password='testpass123')
    u.role = 'agent'
    u.email_verified = True
    u.save()
    return u


def make_property(owner):
    from properties.models import Property
    _counter[0] += 1
    return Property.objects.create(
        title=f'HK Property {_counter[0]}', slug=f'hk-property-{_counter[0]}',
        property_type='apartment', listing_type='rent', status='available',
        price=2500, address='HK St', city='Machakos', country='Kenya',
        owner=owner, bedrooms=1, bathrooms=1, area=30
    )


class CleaningTaskModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.prop = make_property(self.user)
        self.staff = HousekeepingStaff.objects.create(name='Jane Cleaner', phone='+254700000000', managed_by=self.user)

    def test_task_creation(self):
        """Can create a cleaning task."""
        t = CleaningTask.objects.create(
            asset_property=self.prop, task_type='checkout_clean',
            scheduled_date=timezone.now().date(), created_by=self.user
        )
        self.assertEqual(t.status, 'scheduled')
        self.assertEqual(t.task_type, 'checkout_clean')

    def test_default_status_scheduled(self):
        """Default task status is scheduled."""
        t = CleaningTask.objects.create(asset_property=self.prop, scheduled_date=timezone.now().date())
        self.assertEqual(t.status, 'scheduled')

    def test_priority_badge_class(self):
        """Priority badge class maps correctly."""
        t = CleaningTask.objects.create(asset_property=self.prop, scheduled_date=timezone.now().date(), priority='urgent')
        self.assertEqual(t.get_priority_badge_class(), 'danger')
        t.priority = 'low'
        self.assertEqual(t.get_priority_badge_class(), 'secondary')

    def test_str_representation(self):
        """__str__ includes property and task type."""
        t = CleaningTask.objects.create(
            asset_property=self.prop, task_type='routine', scheduled_date=timezone.now().date()
        )
        s = str(t)
        self.assertIn('HK Property', s)
        self.assertIn('Routine', s)

    def test_task_with_assignment(self):
        """Task can be assigned to staff."""
        t = CleaningTask.objects.create(
            asset_property=self.prop, assigned_to=self.staff,
            scheduled_date=timezone.now().date()
        )
        self.assertEqual(t.assigned_to.name, 'Jane Cleaner')


class MaintenanceRequestModelTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.prop = make_property(self.user)

    def test_request_creation(self):
        """Can create a maintenance request."""
        r = MaintenanceRequest.objects.create(
            asset_property=self.prop, title='Leaking tap', description='Bathroom tap leaks',
            category='plumbing', priority='high', reported_by='Guest'
        )
        self.assertEqual(r.status, 'open')
        self.assertEqual(r.category, 'plumbing')

    def test_default_status_open(self):
        """Default status is open."""
        r = MaintenanceRequest.objects.create(
            asset_property=self.prop, title='Test', description='Test',
            category='other', reported_by='Test'
        )
        self.assertEqual(r.status, 'open')

    def test_str_includes_title(self):
        """__str__ includes title and status."""
        r = MaintenanceRequest.objects.create(
            asset_property=self.prop, title='Broken AC', description='AC not cooling',
            category='hvac', reported_by='Manager'
        )
        s = str(r)
        self.assertIn('Broken AC', s)

    def test_priority_choices(self):
        """Priority choices are valid."""
        r = MaintenanceRequest.objects.create(
            asset_property=self.prop, title='Urgent Fix', description='Test',
            category='electrical', priority='urgent', reported_by='Manager'
        )
        self.assertEqual(r.priority, 'urgent')


class HousekeepingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.prop = make_property(self.user)
        self.client.force_login(self.user)

    def test_dashboard_200(self):
        resp = self.client.get(reverse('housekeeping:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_task_list_200(self):
        resp = self.client.get(reverse('housekeeping:task_list'))
        self.assertEqual(resp.status_code, 200)

    def test_create_task_get(self):
        resp = self.client.get(reverse('housekeeping:task_create'))
        self.assertEqual(resp.status_code, 200)

    def test_create_task_post(self):
        count = CleaningTask.objects.count()
        resp = self.client.post(reverse('housekeeping:task_create'), {
            'asset_property': self.prop.pk,
            'task_type': 'checkout_clean',
            'priority': 'normal',
            'scheduled_date': timezone.now().date(),
            'estimated_duration_minutes': 60,
        })
        self.assertGreater(CleaningTask.objects.count(), count)

    def test_update_task_status_ajax(self):
        """AJAX status update returns JSON response."""
        t = CleaningTask.objects.create(asset_property=self.prop, scheduled_date=timezone.now().date())
        resp = self.client.post(
            reverse('housekeeping:task_update_status', kwargs={'pk': t.pk}),
            {'status': 'in_progress'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        t.refresh_from_db()
        self.assertEqual(t.status, 'in_progress')

    def test_maintenance_list_200(self):
        resp = self.client.get(reverse('housekeeping:maintenance_list'))
        self.assertEqual(resp.status_code, 200)

    def test_create_maintenance_get(self):
        resp = self.client.get(reverse('housekeeping:maintenance_create'))
        self.assertEqual(resp.status_code, 200)

    def test_create_maintenance_post(self):
        count = MaintenanceRequest.objects.count()
        self.client.post(reverse('housekeeping:maintenance_create'), {
            'asset_property': self.prop.pk,
            'title': 'Test Issue', 'description': 'Something broken',
            'category': 'other', 'priority': 'medium', 'reported_by': 'Manager'
        })
        self.assertGreater(MaintenanceRequest.objects.count(), count)
