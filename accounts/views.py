from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView, TemplateView, View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
import logging
from .models import User, SavedSearch
from .forms import UserProfileForm, EmailPreferencesForm, PrivacySettingsForm, SavedSearchForm, CustomSignupForm
from properties.models import Property
from messaging.models import PropertyInquiry
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

# Set up logging
logger = logging.getLogger(__name__)

class CustomSignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        
        form = CustomSignupForm()
        return render(request, 'account/signup.html', {'form': form})

    def post(self, request):
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Check if the email is already verified
            if user.email_verified:
                messages.success(request, f'Welcome to Real Estate, {user.get_full_name() or user.email}!')
                return redirect('accounts:dashboard')
            else:
                messages.success(request, 'Welcome to Real Estate! Please verify your email address.')
                return redirect('accounts:email_verification_sent')
        
        return render(request, 'account/signup.html', {'form': form})

class CustomLoginView(View):
    def get(self, request):
        logger.info("GET request to login view")
        logger.info(f"User is authenticated: {request.user.is_authenticated}")
        logger.info(f"Session ID: {request.session.session_key}")
        
        if request.user.is_authenticated:
            logger.info("User is already authenticated, redirecting to dashboard")
            return redirect('accounts:dashboard')
            
        form = AuthenticationForm()
        return render(request, 'account/login.html', {'form': form})

    def post(self, request):
        logger.info("POST request to login view")
        logger.info(f"POST data: {request.POST}")
        
        form = AuthenticationForm(data=request.POST)
        logger.info(f"Form is valid: {form.is_valid()}")
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            logger.info(f"Attempting to authenticate user: {username}")
            
            user = authenticate(username=username, password=password)
            logger.info(f"Authentication result: {user}")
            
            if user is not None:
                logger.info("User authenticated successfully")
                login(request, user)
                logger.info(f"User logged in. Session ID: {request.session.session_key}")
                logger.info(f"User is authenticated after login: {request.user.is_authenticated}")
                
                messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
                
                # Try both ways of redirecting
                response = redirect('accounts:dashboard')
                logger.info(f"Redirect URL: {response.url}")
                return response
            else:
                logger.error("Authentication failed for valid form")
                messages.error(request, 'Invalid username or password.')
        else:
            logger.error(f"Form errors: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
            
        return render(request, 'account/login.html', {'form': form})

@method_decorator([sensitive_post_parameters(), csrf_protect, login_required], name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'Your password was successfully updated!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'account/password_change_done.html'

class EmailVerificationSentView(TemplateView):
    template_name = 'account/verification_sent.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard/dashboard.html'
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        logger.info("Dashboard dispatch called")
        logger.info(f"User authenticated: {request.user.is_authenticated}")
        logger.info(f"Session ID: {request.session.session_key}")
        
        if not request.user.is_authenticated:
            logger.warning("User not authenticated, redirecting to login")
            return redirect('account_login')
            
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        logger.info("Dashboard GET called")
        logger.info(f"User: {request.user}")
        logger.info(f"Session ID: {request.session.session_key}")
        
        # Test if we can even reach this point
        if request.GET.get('test'):
            return HttpResponse("Dashboard is accessible!")
            
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        logger.info("Getting dashboard context data")
        context = super().get_context_data(**kwargs)
        user = self.request.user
        logger.info(f"Dashboard user: {user}")

        try:
            # Common data for all users
            context['recent_inquiries'] = user.property_inquiries.select_related('property').order_by('-created_at')[:5]
            context['favorite_properties'] = user.favorite_properties.all()[:4]
            context['saved_searches'] = user.saved_searches.all()[:3]

            # Agent-specific data
            if user.role == 'agent':
                # Properties owned by the agent
                owned_properties = Property.objects.filter(owner=user)
                # Properties managed by the agent but owned by others
                managed_properties = Property.objects.filter(agent=user).exclude(owner=user)
                # Combine both querysets
                all_agent_properties = owned_properties | managed_properties
                
                context['total_listings'] = all_agent_properties.count()
                context['active_listings'] = all_agent_properties.filter(status='available').count()
                context['total_inquiries'] = PropertyInquiry.objects.filter(
                    property__in=all_agent_properties
                ).count()
                context['recent_listings'] = all_agent_properties.order_by('-created_at')[:5]
            
            # Seller-specific data
            elif user.role == 'seller':
                context['total_listings'] = Property.objects.filter(owner=user).count()
                context['active_listings'] = Property.objects.filter(owner=user, status='available').count()
                context['total_inquiries'] = PropertyInquiry.objects.filter(property__owner=user).count()
                context['recent_listings'] = Property.objects.filter(owner=user).order_by('-created_at')[:5]
                # Add agent-managed properties if any
                context['agent_managed_properties'] = Property.objects.filter(
                    owner=user,
                    agent__isnull=False
                ).select_related('agent')
            
            # Buyer-specific data
            else:
                context['recommended_properties'] = Property.objects.filter(
                    status='available',
                    property_type=user.saved_searches.values_list('property_type', flat=True).first()
                )[:4]
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            messages.error(self.request, "There was an error loading your dashboard data.")
            context['error'] = True

        return context

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['favorite_properties'] = user.favorite_properties.all()[:4]
        context['saved_searches'] = user.saved_searches.all()[:4]
        context['recent_inquiries'] = user.property_inquiries.select_related('property').order_by('-created_at')[:4]
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class EmailPreferencesView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = EmailPreferencesForm
    template_name = 'accounts/email_preferences.html'
    success_url = reverse_lazy('accounts:email_preferences')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Email preferences updated successfully!')
        return super().form_valid(form)

class PrivacySettingsView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = PrivacySettingsForm
    template_name = 'accounts/privacy_settings.html'
    success_url = reverse_lazy('accounts:privacy_settings')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Privacy settings updated successfully!')
        return super().form_valid(form)

class FavoritePropertiesView(LoginRequiredMixin, ListView):
    template_name = 'accounts/dashboard/favorites.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        return self.request.user.favorite_properties.all()

class SavedSearchesView(LoginRequiredMixin, ListView):
    model = SavedSearch
    template_name = 'accounts/dashboard/saved_searches.html'
    context_object_name = 'saved_searches'
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.saved_searches.all()

class UserInquiriesView(LoginRequiredMixin, ListView):
    template_name = 'accounts/dashboard/inquiries.html'
    context_object_name = 'inquiries'
    paginate_by = 20

    def get_queryset(self):
        return PropertyInquiry.objects.filter(user=self.request.user).select_related('property')

class UserReviewsView(LoginRequiredMixin, ListView):
    template_name = 'accounts/dashboard/reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        return self.request.user.property_reviews.select_related('property')

class SaveSearchView(LoginRequiredMixin, CreateView):
    model = SavedSearch
    form_class = SavedSearchForm
    template_name = 'accounts/dashboard/save_search.html'
    success_url = reverse_lazy('accounts:saved_searches')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Search saved successfully!')
        return super().form_valid(form)

class DeleteSearchView(LoginRequiredMixin, DeleteView):
    model = SavedSearch
    template_name = 'accounts/dashboard/delete_search.html'
    success_url = reverse_lazy('accounts:saved_searches')

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Search deleted successfully!')
        return super().delete(request, *args, **kwargs)

class EditSearchView(LoginRequiredMixin, UpdateView):
    model = SavedSearch
    form_class = SavedSearchForm
    template_name = 'accounts/dashboard/edit_search.html'
    success_url = reverse_lazy('accounts:saved_searches')

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Search updated successfully!')
        return super().form_valid(form)

class ResendVerificationEmailView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            email_address = EmailAddress.objects.get(user=request.user, primary=True)
            if email_address.verified:
                messages.info(request, 'Your email is already verified.')
            else:
                send_email_confirmation(request, request.user)
                messages.success(request, 'Verification email has been sent.')
        except EmailAddress.DoesNotExist:
            # Create email address record if it doesn't exist
            EmailAddress.objects.create(
                user=request.user,
                email=request.user.email,
                primary=True,
                verified=False
            )
            send_email_confirmation(request, request.user)
            messages.success(request, 'Verification email has been sent.')
        
        return redirect('accounts:email_verification_sent')
