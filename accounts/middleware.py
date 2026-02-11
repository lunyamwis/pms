from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from allauth.account.models import EmailAddress

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last active timestamp
            request.user.update_last_active()
            
            # Store IP address on login
            if not hasattr(request, '_security_middleware_applied'):
                request.user.last_login_ip = request.META.get('REMOTE_ADDR')
                request.user.save()
                request._security_middleware_applied = True
            
            # Check if account is locked
            if request.user.is_account_locked():
                messages.error(request, 'Your account is temporarily locked due to multiple failed login attempts.')
                return redirect('accounts:login')
            
            # Define exempt paths that bypass security checks
            exempt_paths = [
                '/accounts/login/',
                '/accounts/logout/',
                '/accounts/password/change/',
                '/accounts/password_change/',
                '/accounts/email/verification/',  # Changed to match all verification paths
                '/static/',  # Static files should bypass
                '/media/',  # Media files should bypass
            ]
            
            # Check if current path is exempt
            current_path = request.path
            if any(current_path.startswith(path) for path in exempt_paths):
                return self.get_response(request)
            
            # Check if email is verified in allauth
            email_address = EmailAddress.objects.filter(email=request.user.email).first()
            if email_address and email_address.verified and not request.user.email_verified:
                request.user.email_verified = True
                request.user.save()
            
            # Check if email verification is required and not already verified
            if not request.user.email_verified and not current_path.startswith('/accounts/email/verification/'):
                messages.warning(request, 'Please verify your email address to access all features.')
                return redirect('accounts:email_verification_sent')
            
            # Check if password change is required
            if request.user.requires_password_change:
                if not current_path.startswith('/accounts/password/'):
                    messages.warning(request, 'Your password has expired. Please change it to continue.')
                    return redirect('accounts:password_change')
            
            # Check if 2FA is required for sensitive operations
            sensitive_paths = [
                '/accounts/settings/',
                '/accounts/password/change/',
                '/properties/create/',
                '/properties/edit/',
            ]
            if any(request.path.startswith(path) for path in sensitive_paths):
                if request.user.two_factor_enabled and not request.session.get('2fa_verified'):
                    return redirect('account_2fa_verify')

        response = self.get_response(request)
        return response

class ActivityTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            # Update last active timestamp
            request.user.update_last_active()
            
            # Track user activity
            if hasattr(request, 'session'):
                # Store last 10 pages visited
                visited_pages = request.session.get('visited_pages', [])
                if request.path not in visited_pages:
                    visited_pages.insert(0, {
                        'path': request.path,
                        'timestamp': timezone.now().isoformat(),
                        'method': request.method
                    })
                    visited_pages = visited_pages[:10]  # Keep only last 10
                    request.session['visited_pages'] = visited_pages
                
                # Track session duration
                if not request.session.get('session_start'):
                    request.session['session_start'] = timezone.now().isoformat()
        
        return response 