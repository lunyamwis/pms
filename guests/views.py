import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import HttpResponse
from django.db.models import Q, Sum

from .models import Guest, GuestDocument
from .forms import GuestForm, GuestSearchForm, GuestDocumentForm


class GuestListView(LoginRequiredMixin, ListView):
    model = Guest
    template_name = 'guests/guest_list.html'
    context_object_name = 'guests'
    paginate_by = 25

    def get_queryset(self):
        qs = Guest.objects.all()
        form = GuestSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('search'):
                q = form.cleaned_data['search']
                qs = qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(email__icontains=q)|Q(phone__icontains=q))
            f = form.cleaned_data.get('filter', 'all')
            if f == 'vip':
                qs = qs.filter(is_vip=True)
            elif f == 'repeat':
                qs = qs.filter(bookings__status='checked_out').distinct().annotate(
                    stay_count=Sum('bookings__total_nights')
                ).filter(stay_count__gt=1)
            elif f == 'blacklisted':
                qs = qs.filter(is_blacklisted=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = GuestSearchForm(self.request.GET)
        return ctx


class GuestDetailView(LoginRequiredMixin, DetailView):
    model = Guest
    template_name = 'guests/guest_detail.html'
    context_object_name = 'guest'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['doc_form'] = GuestDocumentForm()
        ctx['bookings'] = self.object.bookings.select_related('asset_property' ).order_by('-check_in_date')
        return ctx


class GuestCreateView(LoginRequiredMixin, CreateView):
    model = Guest
    form_class = GuestForm
    template_name = 'guests/guest_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Guest profile created.')
        return super().form_valid(form)


class GuestUpdateView(LoginRequiredMixin, UpdateView):
    model = Guest
    form_class = GuestForm
    template_name = 'guests/guest_form.html'


class GuestBlacklistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        if guest.is_blacklisted:
            guest.is_blacklisted = False
            guest.blacklist_reason = ''
            messages.info(request, f'{guest.full_name} removed from blacklist.')
        else:
            reason = request.POST.get('reason', '')
            guest.is_blacklisted = True
            guest.blacklist_reason = reason
            messages.warning(request, f'{guest.full_name} added to blacklist.')
        guest.save()
        return redirect('guests:detail', pk=pk)


class GuestDocumentUploadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        form = GuestDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.guest = guest
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, 'Document uploaded.')
        return redirect('guests:detail', pk=pk)


class GuestExportView(LoginRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="guests.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Phone', 'Nationality', 'Total Bookings', 'Total Spent', 'VIP', 'Blacklisted'])
        for g in Guest.objects.all():
            writer.writerow([g.full_name, g.email, g.phone, g.nationality, g.total_bookings, g.total_spent, g.is_vip, g.is_blacklisted])
        return response
