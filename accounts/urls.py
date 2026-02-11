from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from . import views

app_name = 'accounts'

def test_view(request):
    return HttpResponse(f"Test view - User authenticated: {request.user.is_authenticated}, User: {request.user}")

urlpatterns = [
    # Test URL
    path('test/', test_view, name='test'),
    
    # Authentication - Custom Views
    path('signup/', views.CustomSignupView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    
    # Authentication - AllAuth Compatibility
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='account_change_password'),
    path('password/change/done/', views.CustomPasswordChangeDoneView.as_view(), name='account_change_password_done'),
    path('email/verification/sent/', views.EmailVerificationSentView.as_view(), name='email_verification_sent'),
    path('email/verification/resend/', views.ResendVerificationEmailView.as_view(), name='resend_verification_email'),
    
    # Password Reset
    path('password/reset/', auth_views.PasswordResetView.as_view(
        template_name='account/password_reset.html',
        email_template_name='account/email/password_reset_email.html',
        subject_template_name='account/email/password_reset_subject.txt'
    ), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html'
    ), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='account/password_reset_from_key.html'
    ), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='account/password_reset_from_key_done.html'
    ), name='password_reset_complete'),
    
    path('', include('allauth.urls')),  # Include all allauth URLs
    
    # Dashboard
    path('dashboard/', login_required(views.DashboardView.as_view()), name='dashboard'),
    
    # Profile
    path('profile/', login_required(views.ProfileView.as_view()), name='profile'),
    path('profile/edit/', login_required(views.ProfileUpdateView.as_view()), name='profile_edit'),
    path('profile/email/', login_required(views.EmailPreferencesView.as_view()), name='email_preferences'),
    path('profile/privacy/', login_required(views.PrivacySettingsView.as_view()), name='privacy_settings'),
    
    # Inquiries
    path('inquiries/', login_required(views.UserInquiriesView.as_view()), name='inquiries'),

    # Favorites and saved searches
    path('favorites/', login_required(views.FavoritePropertiesView.as_view()), name='favorites'),
    path('searches/', login_required(views.SavedSearchesView.as_view()), name='saved_searches'),
    path('searches/save/', login_required(views.SaveSearchView.as_view()), name='save_search'),
] 