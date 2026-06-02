import csv
import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from django.urls import reverse_lazy

from .models import CashbookEntry, Receipt, Budget
from .forms import CashbookEntryForm, DateRangeForm, OpeningBalanceForm


class FinancialDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'financials/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        entries = CashbookEntry.objects.all()
        month_entries = entries.filter(date__gte=month_start)
        ctx['month_income'] = month_entries.filter(entry_type='receipt').aggregate(t=Sum('amount'))['t'] or 0
        ctx['month_expense'] = month_entries.filter(entry_type='payment').aggregate(t=Sum('amount'))['t'] or 0
        ctx['month_profit'] = ctx['month_income'] - ctx['month_expense']
        latest = entries.order_by('-date','-created_at').first()
        ctx['current_balance'] = latest.balance if latest else Decimal('0')
        ctx['recent_entries'] = entries.order_by('-date','-created_at')[:10]
        return ctx


class CashbookView(LoginRequiredMixin, TemplateView):
    template_name = 'financials/cashbook.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = DateRangeForm(self.request.GET)
        qs = CashbookEntry.objects.all().order_by('date','created_at')
        if form.is_valid():
            if form.cleaned_data.get('date_from'):
                qs = qs.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                qs = qs.filter(date__lte=form.cleaned_data['date_to'])
            if form.cleaned_data.get('category'):
                qs = qs.filter(category=form.cleaned_data['category'])
        ctx['entries'] = qs
        ctx['filter_form'] = form
        ctx['entry_form'] = CashbookEntryForm()
        agg = qs.aggregate(
            total_receipts=Sum('amount', filter=Q(entry_type='receipt')),
            total_payments=Sum('amount', filter=Q(entry_type='payment')),
        )
        ctx['total_receipts'] = agg['total_receipts'] or Decimal('0')
        ctx['total_payments'] = agg['total_payments'] or Decimal('0')
        ctx['net_balance'] = ctx['total_receipts'] - ctx['total_payments']
        latest = qs.order_by('-date','-created_at').first()
        ctx['current_balance'] = latest.balance if latest else Decimal('0')
        return ctx


class CashbookEntryCreateView(LoginRequiredMixin, CreateView):
    model = CashbookEntry
    form_class = CashbookEntryForm
    template_name = 'financials/entry_form.html'
    success_url = reverse_lazy('financials:cashbook')

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, 'Entry added to cashbook.')
        return super().form_valid(form)


class CashbookEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = CashbookEntry
    form_class = CashbookEntryForm
    template_name = 'financials/entry_form.html'
    success_url = reverse_lazy('financials:cashbook')


class CashbookEntryDeleteView(LoginRequiredMixin, DeleteView):
    model = CashbookEntry
    template_name = 'financials/entry_confirm_delete.html'
    success_url = reverse_lazy('financials:cashbook')


class ReceiptListView(LoginRequiredMixin, ListView):
    model = Receipt
    template_name = 'financials/receipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 20


class ReceiptDetailView(LoginRequiredMixin, DetailView):
    model = Receipt
    template_name = 'financials/receipt_detail.html'
    context_object_name = 'receipt'


class FinancialReportView(LoginRequiredMixin, TemplateView):
    template_name = 'financials/report.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year = int(self.request.GET.get('year', timezone.now().year))
        entries = CashbookEntry.objects.filter(date__year=year)
        monthly_data = []
        for month in range(1, 13):
            me = entries.filter(date__month=month)
            income = float(me.filter(entry_type='receipt').aggregate(t=Sum('amount'))['t'] or 0)
            expense = float(me.filter(entry_type='payment').aggregate(t=Sum('amount'))['t'] or 0)
            monthly_data.append({'month': month, 'income': income, 'expense': expense, 'profit': income - expense})
        ctx['monthly_data'] = monthly_data
        ctx['year'] = year
        ctx['total_income'] = entries.filter(entry_type='receipt').aggregate(t=Sum('amount'))['t'] or 0
        ctx['total_expense'] = entries.filter(entry_type='payment').aggregate(t=Sum('amount'))['t'] or 0
        return ctx


class ExportCashbookView(LoginRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="cashbook_{timezone.now().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date','Name','Description','Category','Receipt (KES)','Payment (KES)','Balance (KES)','Reference'])
        for e in CashbookEntry.objects.all().order_by('date','created_at'):
            r = e.amount if e.entry_type == 'receipt' else ''
            p = e.amount if e.entry_type == 'payment' else ''
            writer.writerow([e.date, e.name, e.description, e.get_category_display(), r, p, e.balance, e.reference])
        return response


class SetOpeningBalanceView(LoginRequiredMixin, View):
    def post(self, request):
        form = OpeningBalanceForm(request.POST)
        if form.is_valid():
            CashbookEntry.objects.create(
                date=form.cleaned_data['date'], name='Opening Balance',
                description='Balance B/F', entry_type='receipt',
                category='other_income', amount=form.cleaned_data['amount'],
                is_opening_balance=True, recorded_by=request.user,
            )
            messages.success(request, 'Opening balance set.')
        return redirect('financials:cashbook')


class FinancialChartDataView(LoginRequiredMixin, View):
    def get(self, request):
        from dateutil.relativedelta import relativedelta
        months = []
        for i in range(6, -1, -1):
            d = timezone.now().date().replace(day=1) - relativedelta(months=i)
            me = CashbookEntry.objects.filter(date__year=d.year, date__month=d.month)
            income = float(me.filter(entry_type='receipt').aggregate(t=Sum('amount'))['t'] or 0)
            expense = float(me.filter(entry_type='payment').aggregate(t=Sum('amount'))['t'] or 0)
            months.append({'label': d.strftime('%b %Y'), 'income': income, 'expense': expense})
        return JsonResponse(months, safe=False)
