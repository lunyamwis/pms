import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import BookingComProperty, AirbnbProperty, WhatsAppConfig, MessageTemplate, IntegrationLog

logger = logging.getLogger(__name__)


class IntegrationsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'integrations/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['bookingcom_configs'] = BookingComProperty.objects.filter(user=self.request.user)
        ctx['airbnb_configs'] = AirbnbProperty.objects.filter(user=self.request.user)
        ctx['whatsapp_configs'] = WhatsAppConfig.objects.filter(user=self.request.user)
        ctx['recent_logs'] = IntegrationLog.objects.order_by('-created_at')[:20]
        return ctx


class BookingComSetupView(LoginRequiredMixin, View):
    template_name = 'integrations/bookingcom_setup.html'

    def get(self, request):
        configs = BookingComProperty.objects.filter(user=request.user)
        return render(request, self.template_name, {'configs': configs})

    def post(self, request):
        from properties.models import Property
        prop_id = request.POST.get('booking_property')
        hotel_id = request.POST.get('hotel_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            prop = Property.objects.get(pk=prop_id)
            config, _ = BookingComProperty.objects.update_or_create(
                user=request.user, property=prop,
                defaults={'hotel_id': hotel_id, 'username': username, 'password': password, 'is_connected': True}
            )
            messages.success(request, f'Booking.com connected for {prop.title}')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('integrations:bookingcom_setup')


@method_decorator(csrf_exempt, name='dispatch')
class BookingComWebhookView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            from integrations.tasks import process_booking_com_webhook
            process_booking_com_webhook.delay(payload)
        except Exception as e:
            logger.error(f'Booking.com webhook error: {e}')
        return HttpResponse('OK')


class AirbnbSetupView(LoginRequiredMixin, View):
    template_name = 'integrations/airbnb_setup.html'

    def get(self, request):
        configs = AirbnbProperty.objects.filter(user=request.user)
        return render(request, self.template_name, {'configs': configs})

    def post(self, request):
        from properties.models import Property
        prop_id = request.POST.get('booking_property')
        listing_id = request.POST.get('listing_id')
        access_token = request.POST.get('access_token')
        try:
            prop = Property.objects.get(pk=prop_id)
            AirbnbProperty.objects.update_or_create(
                user=request.user, property=prop,
                defaults={'listing_id': listing_id, 'access_token': access_token, 'is_connected': True}
            )
            messages.success(request, f'Airbnb connected for {prop.title}')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('integrations:airbnb_setup')


@method_decorator(csrf_exempt, name='dispatch')
class AirbnbWebhookView(View):
    def post(self, request):
        return HttpResponse('OK')


class WhatsAppSetupView(LoginRequiredMixin, View):
    template_name = 'integrations/whatsapp_setup.html'

    def get(self, request):
        config = WhatsAppConfig.objects.filter(user=request.user).first()
        return render(request, self.template_name, {'config': config})

    def post(self, request):
        WhatsAppConfig.objects.update_or_create(
            user=request.user, property=None,
            defaults={
                'account_sid': request.POST.get('account_sid'),
                'auth_token': request.POST.get('auth_token'),
                'from_number': request.POST.get('from_number'),
                'is_active': True,
            }
        )
        messages.success(request, 'WhatsApp configured successfully.')
        return redirect('integrations:dashboard')


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    def post(self, request):
        from_number = request.POST.get('From', '')
        body = request.POST.get('Body', '')
        logger.info(f'WhatsApp incoming: {from_number}: {body}')
        # Match to booking by phone number
        try:
            from guests.models import Guest
            from bookings.models import Booking, BookingMessage
            phone = from_number.replace('whatsapp:', '')
            guest = Guest.objects.filter(phone=phone).first() or Guest.objects.filter(whatsapp_number=phone).first()
            if guest:
                booking = guest.bookings.filter(status__in=['confirmed', 'checked_in']).order_by('-check_in_date').first()
                if booking:
                    BookingMessage.objects.create(
                        booking=booking, direction='inbound', channel='whatsapp',
                        sender_name=guest.full_name, content=body, status='read'
                    )
        except Exception as e:
            logger.error(f'WhatsApp webhook processing error: {e}')
        return HttpResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', content_type='text/xml')


class MessageTemplateListView(LoginRequiredMixin, ListView):
    model = MessageTemplate
    template_name = 'integrations/message_templates.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return MessageTemplate.objects.filter(user=self.request.user) | MessageTemplate.objects.filter(user=None, is_default=True)


class MessageTemplateCreateView(LoginRequiredMixin, CreateView):
    model = MessageTemplate
    fields = ['template_type', 'name', 'subject', 'body', 'channel', 'is_active']
    template_name = 'integrations/template_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Template created.')
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('integrations:templates')


class MessageTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = MessageTemplate
    fields = ['name', 'subject', 'body', 'channel', 'is_active']
    template_name = 'integrations/template_form.html'

    def get_success_url(self):
        from django.urls import reverse
        return reverse('integrations:templates')


class SyncReservationsView(LoginRequiredMixin, View):
    def post(self, request):
        from integrations.tasks import sync_all_booking_com, sync_all_airbnb
        sync_all_booking_com.delay()
        sync_all_airbnb.delay()
        messages.success(request, 'Sync started. Reservations will be updated shortly.')
        return redirect('integrations:dashboard')


class IntegrationLogView(LoginRequiredMixin, ListView):
    model = IntegrationLog
    template_name = 'integrations/logs.html'
    context_object_name = 'logs'
    paginate_by = 50
