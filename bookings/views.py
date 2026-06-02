import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.urls import reverse_lazy

from .models import Booking, BookingPayment, BookingMessage, BookingNote
from .forms import BookingForm, CheckInForm, CheckOutForm, PaymentForm, BookingNoteForm, BookingSearchForm


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20

    def get_queryset(self):
        qs = Booking.objects.filter(
            managed_by=self.request.user
        ).select_related('guest', 'asset_property' , 'unit')
        form = BookingSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('search'):
                q = form.cleaned_data['search']
                qs = qs.filter(
                    Q(booking_reference__icontains=q) |
                    Q(guest__first_name__icontains=q) |
                    Q(guest__last_name__icontains=q) |
                    Q(guest__phone__icontains=q)
                )
            if form.cleaned_data.get('status'):
                qs = qs.filter(status__in=form.cleaned_data['status'])
            if form.cleaned_data.get('source'):
                qs = qs.filter(source=form.cleaned_data['source'])
            if form.cleaned_data.get('date_from'):
                qs = qs.filter(check_in_date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                qs = qs.filter(check_in_date__lte=form.cleaned_data['date_to'])
            sort = form.cleaned_data.get('sort') or '-created_at'
            qs = qs.order_by(sort)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = BookingSearchForm(self.request.GET)
        today = timezone.now().date()
        base_qs = Booking.objects.filter(managed_by=self.request.user)
        ctx['stats'] = {
            'total': base_qs.count(),
            'confirmed': base_qs.filter(status='confirmed').count(),
            'checked_in': base_qs.filter(status='checked_in').count(),
            'checkout_today': base_qs.filter(status='checked_in', check_out_date=today).count(),
        }
        return ctx


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['note_form'] = BookingNoteForm()
        ctx['payment_form'] = PaymentForm()
        return ctx


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'

    def form_valid(self, form):
        form.instance.managed_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Booking {self.object.booking_reference} created successfully.')
        # Trigger confirmation message task
        try:
            from integrations.tasks import send_booking_confirmation
            send_booking_confirmation.delay(self.object.pk)
        except Exception:
            pass
        return response

    def get_success_url(self):
        return reverse_lazy('bookings:detail', kwargs={'pk': self.object.pk})


class BookingUpdateView(LoginRequiredMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'

    def get_success_url(self):
        return reverse_lazy('bookings:detail', kwargs={'pk': self.object.pk})


class BookingCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        reason = request.POST.get('reason', '')
        booking.status = Booking.STATUS_CANCELLED
        booking.internal_notes += f'\n[CANCELLED] {reason}'
        booking.save()
        messages.warning(request, f'Booking {booking.booking_reference} has been cancelled.')
        return redirect('bookings:detail', pk=pk)


class CheckInView(LoginRequiredMixin, View):
    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        form = CheckInForm(instance=booking)
        return render(request, 'bookings/checkin_form.html', {'booking': booking, 'form': form})

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        form = CheckInForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = Booking.STATUS_CHECKED_IN
            booking.check_in_time = form.cleaned_data.get('check_in_time') or timezone.now().time()
            booking.save()
            messages.success(request, f'{booking.guest.full_name} has been checked in.')
            return redirect('bookings:detail', pk=pk)
        return render(request, 'bookings/checkin_form.html', {'booking': booking, 'form': form})


class CheckOutView(LoginRequiredMixin, View):
    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        form = CheckOutForm(instance=booking)
        return render(request, 'bookings/checkout_form.html', {'booking': booking, 'form': form})

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        form = CheckOutForm(request.POST, instance=booking)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.status = Booking.STATUS_CHECKED_OUT
            booking.check_out_time = form.cleaned_data.get('check_out_time') or timezone.now().time()
            booking.save()
            messages.success(request, f'{booking.guest.full_name} has been checked out.')
            # Auto-create cleaning task and send review request
            try:
                from housekeeping.models import CleaningTask
                CleaningTask.objects.create(
                    asset_property=booking.asset_property,
                    unit=booking.unit,
                    booking=booking,
                    task_type='checkout_clean',
                    scheduled_date=timezone.now().date(),
                    priority='high',
                    created_by=request.user,
                )
            except Exception:
                pass
            try:
                from integrations.tasks import send_review_request
                send_review_request.apply_async(
                    args=[booking.pk], countdown=7200  # 2 hours after checkout
                )
                from integrations.tasks import send_receipt
                send_receipt.delay(booking.pk)
            except Exception:
                pass
            return redirect('bookings:detail', pk=pk)
        return render(request, 'bookings/checkout_form.html', {'booking': booking, 'form': form})


class RecordPaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.recorded_by = request.user
            payment.save()
            # Create cashbook entry
            try:
                from financials.models import CashbookEntry
                CashbookEntry.objects.create(
                    date=payment.paid_at.date(),
                    description=f'Payment - {booking.booking_reference}',
                    name=booking.guest.full_name,
                    entry_type='receipt',
                    category='room_booking',
                    amount=payment.amount,
                    asset_property=booking.asset_property,
                    booking=booking,
                    reference=payment.reference_number,
                    payment_method=payment.payment_method,
                    recorded_by=request.user,
                )
            except Exception:
                pass
            messages.success(request, f'Payment of {payment.amount} recorded.')
        else:
            messages.error(request, 'Invalid payment data.')
        return redirect('bookings:detail', pk=pk)


class GenerateReceiptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        from financials.models import Receipt
        receipt, created = Receipt.objects.get_or_create(
            booking=booking,
            defaults={
                'guest_name': booking.guest.full_name,
                'property_name': booking.asset_property.title,
                'check_in_date': booking.check_in_date,
                'check_out_date': booking.check_out_date,
                'room_rate': booking.room_rate,
                'total_nights': booking.total_nights,
                'subtotal': booking.subtotal,
                'cleaning_fee': booking.cleaning_fee,
                'tax_amount': booking.tax_amount,
                'discount_amount': booking.discount_amount,
                'total_amount': booking.total_amount,
                'payment_method': booking.payments.filter(status='completed').first().payment_method if booking.payments.filter(status='completed').exists() else 'cash',
                'issued_by': request.user,
            }
        )
        messages.success(request, f'Receipt {receipt.receipt_number} generated.')
        return redirect('financials:receipt_detail', pk=receipt.pk)


class SendReceiptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        channel = request.POST.get('channel', 'both')
        try:
            from integrations.tasks import send_receipt_task
            send_receipt_task.delay(booking.pk, channel)
            messages.success(request, 'Receipt is being sent.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('bookings:detail', pk=pk)


class SendGuestMessageView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        content = request.POST.get('message', '').strip()
        channel = request.POST.get('channel', 'whatsapp')
        if not content:
            messages.error(request, 'Message cannot be empty.')
            return redirect('bookings:detail', pk=pk)
        try:
            from integrations.tasks import send_custom_message
            send_custom_message.delay(booking.pk, content, channel)
            BookingMessage.objects.create(
                booking=booking,
                direction='outbound',
                channel=channel,
                sender_name=request.user.get_full_name() or request.user.email,
                content=content,
                status='sent',
            )
            messages.success(request, 'Message sent.')
        except Exception as e:
            messages.error(request, f'Failed to send: {e}')
        return redirect('bookings:detail', pk=pk)


class AddBookingNoteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, managed_by=request.user)
        form = BookingNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.booking = booking
            note.author = request.user
            note.save()
            messages.success(request, 'Note added.')
        return redirect('bookings:detail', pk=pk)


class BookingCalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'bookings/booking_calendar.html'


class CalendarEventsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        bookings = Booking.objects.filter(
            managed_by=request.user
        ).select_related('guest', 'asset_property' )
        COLOR_MAP = {
            'pending': '#f59e0b',
            'confirmed': '#3b82f6',
            'checked_in': '#10b981',
            'checked_out': '#6b7280',
            'cancelled': '#ef4444',
            'no_show': '#1f2937',
        }
        events = []
        for b in bookings:
            events.append({
                'id': b.pk,
                'title': f'{b.guest.full_name} - {b.asset_property.title}',
                'start': str(b.check_in_date),
                'end': str(b.check_out_date),
                'color': COLOR_MAP.get(b.status, '#6b7280'),
                'url': b.get_absolute_url(),
                'extendedProps': {'status': b.status, 'reference': b.booking_reference},
            })
        return JsonResponse(events, safe=False)
