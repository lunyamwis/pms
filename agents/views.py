from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, UpdateView, TemplateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Avg, Q
from accounts.models import User
from properties.models import Property
from messaging.models import PropertyInquiry
from .models import Agent

class AgentListView(ListView):
    model = Agent
    template_name = 'agents/agent_list.html'
    context_object_name = 'agents'
    paginate_by = 12

    def get_queryset(self):
        return Agent.objects.annotate(
            properties_count=Count('user__owned_properties') + Count('user__managed_properties'),
            average_rating=Avg('user__property_reviews__rating')
        ).select_related('user').order_by('-properties_count')

class AgentDetailView(DetailView):
    model = Agent
    template_name = 'agents/agent_detail.html'
    context_object_name = 'agent'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent = self.get_object()
        # Get both owned and managed properties
        owned_properties = Property.objects.filter(owner=agent.user)
        managed_properties = Property.objects.filter(agent=agent.user).exclude(owner=agent.user)
        all_properties = (owned_properties | managed_properties).filter(status='available')[:6]
        context['properties'] = all_properties
        context['reviews'] = agent.reviews.select_related('user').order_by('-created_at')[:5]
        return context

class AgentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'agents/dashboard/dashboard.html'

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Get both owned and managed properties
        owned_properties = Property.objects.filter(owner=user)
        managed_properties = Property.objects.filter(agent=user).exclude(owner=user)
        all_properties = owned_properties | managed_properties
        
        context['total_properties'] = all_properties.count()
        context['active_properties'] = all_properties.filter(status='available').count()
        context['total_inquiries'] = PropertyInquiry.objects.filter(
            property__in=all_properties
        ).count()
        context['recent_inquiries'] = PropertyInquiry.objects.filter(
            property__in=all_properties
        ).select_related('user', 'property').order_by('-created_at')[:5]
        return context

class AgentPropertiesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'agents/dashboard/properties.html'
    context_object_name = 'properties'
    paginate_by = 10

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_queryset(self):
        user = self.request.user
        # Get both owned and managed properties
        owned_properties = Property.objects.filter(owner=user)
        managed_properties = Property.objects.filter(agent=user).exclude(owner=user)
        return (owned_properties | managed_properties).order_by('-created_at')

class AgentInquiriesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'agents/dashboard/inquiries.html'
    context_object_name = 'inquiries'
    paginate_by = 20

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_queryset(self):
        user = self.request.user
        # Get inquiries for both owned and managed properties
        return PropertyInquiry.objects.filter(
            Q(property__owner=user) | Q(property__agent=user)
        ).select_related('user', 'property').order_by('-created_at')

class AgentReviewsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'agents/dashboard/reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_queryset(self):
        user = self.request.user
        # Get reviews for both owned and managed properties
        return user.property_reviews.select_related('user').order_by('-created_at')

class AgentMessagesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'agents/dashboard/messages.html'

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_messages'] = self.request.user.received_messages.filter(is_read=False).count()
        context['recent_messages'] = self.request.user.received_messages.select_related('sender').order_by('-created_at')[:5]
        return context

class AgentAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'agents/dashboard/analytics.html'

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Get both owned and managed properties
        owned_properties = Property.objects.filter(owner=user)
        managed_properties = Property.objects.filter(agent=user).exclude(owner=user)
        all_properties = owned_properties | managed_properties
        
        context['property_views'] = all_properties.aggregate(total_views=Count('views_count'))
        context['property_inquiries'] = PropertyInquiry.objects.filter(
            property__in=all_properties
        ).count()
        context['favorite_count'] = all_properties.aggregate(total_favorites=Count('favorited_by'))
        
        # Add separate stats for owned vs managed properties
        context['owned_properties_count'] = owned_properties.count()
        context['managed_properties_count'] = managed_properties.count()
        return context

class AgentProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Agent
    template_name = 'agents/dashboard/profile_edit.html'
    fields = ['bio', 'phone', 'address', 'website', 'social_facebook', 'social_twitter', 'social_linkedin']
    success_url = reverse_lazy('agents:profile_edit')

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_object(self):
        return self.request.user.agent

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class AgentSettingsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Agent
    template_name = 'agents/dashboard/settings.html'
    fields = ['notification_preferences', 'email_preferences']
    success_url = reverse_lazy('agents:settings')

    def test_func(self):
        return self.request.user.role == 'agent'

    def get_object(self):
        return self.request.user.agent

    def form_valid(self, form):
        messages.success(self.request, 'Settings updated successfully!')
        return super().form_valid(form)
