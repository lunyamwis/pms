from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.http import JsonResponse
from django.utils import timezone

from .models import CleaningTask, MaintenanceRequest, RoomServiceOrder, HousekeepingStaff
from .forms import CleaningTaskForm, MaintenanceRequestForm, HousekeepingStaffForm


class HousekeepingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'housekeeping/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        ctx['todays_tasks'] = CleaningTask.objects.filter(scheduled_date=today).select_related('booking_property', 'assigned_to')
        ctx['urgent_maintenance'] = MaintenanceRequest.objects.filter(priority='urgent', status__in=['open', 'assigned']).select_related('booking_property')
        ctx['pending_room_service'] = RoomServiceOrder.objects.filter(status='pending').select_related('booking')
        ctx['stats'] = {
            'tasks_today': CleaningTask.objects.filter(scheduled_date=today).count(),
            'tasks_completed': CleaningTask.objects.filter(scheduled_date=today, status='completed').count(),
            'open_maintenance': MaintenanceRequest.objects.filter(status__in=['open', 'assigned']).count(),
            'pending_orders': RoomServiceOrder.objects.filter(status='pending').count(),
        }
        return ctx


class CleaningTaskListView(LoginRequiredMixin, ListView):
    model = CleaningTask
    template_name = 'housekeeping/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('booking_property', 'assigned_to', 'booking')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class CleaningTaskDetailView(LoginRequiredMixin, DetailView):
    model = CleaningTask
    template_name = 'housekeeping/task_detail.html'
    context_object_name = 'task'


class CleaningTaskCreateView(LoginRequiredMixin, CreateView):
    model = CleaningTask
    form_class = CleaningTaskForm
    template_name = 'housekeeping/task_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Cleaning task scheduled.')
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('housekeeping:task_list')


class UpdateTaskStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(CleaningTask, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(CleaningTask.STATUS_CHOICES):
            task.status = new_status
            if new_status == 'in_progress':
                task.started_at = timezone.now()
            elif new_status == 'completed':
                task.completed_at = timezone.now()
            task.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'status': task.status})
        return redirect('housekeeping:task_list')


class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    model = MaintenanceRequest
    template_name = 'housekeeping/maintenance_list.html'
    context_object_name = 'requests'
    paginate_by = 20


class MaintenanceRequestDetailView(LoginRequiredMixin, DetailView):
    model = MaintenanceRequest
    template_name = 'housekeeping/maintenance_detail.html'
    context_object_name = 'request'


class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceRequest
    form_class = MaintenanceRequestForm
    template_name = 'housekeeping/maintenance_form.html'

    def get_success_url(self):
        from django.urls import reverse
        return reverse('housekeeping:maintenance_list')


class MaintenanceRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = MaintenanceRequest
    fields = ['status', 'assigned_to', 'actual_cost', 'resolution_notes']
    template_name = 'housekeeping/maintenance_form.html'

    def get_success_url(self):
        return self.object.get_absolute_url() if hasattr(self.object, 'get_absolute_url') else '/'


class RoomServiceListView(LoginRequiredMixin, ListView):
    model = RoomServiceOrder
    template_name = 'housekeeping/room_service_list.html'
    context_object_name = 'orders'
    paginate_by = 20


class StaffListView(LoginRequiredMixin, ListView):
    model = HousekeepingStaff
    template_name = 'housekeeping/staff_list.html'
    context_object_name = 'staff'

    def get_queryset(self):
        return super().get_queryset().filter(managed_by=self.request.user)


class StaffCreateView(LoginRequiredMixin, CreateView):
    model = HousekeepingStaff
    form_class = HousekeepingStaffForm
    template_name = 'housekeeping/staff_form.html'

    def form_valid(self, form):
        form.instance.managed_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('housekeeping:staff_list')
