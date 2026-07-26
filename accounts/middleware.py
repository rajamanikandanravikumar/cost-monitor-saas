from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.utils import timezone

class ActiveSessionEnforcementMiddleware:
    """
    Middleware to ensure that logged-in users who have been removed (is_active=False),
    have lost their Profile, or whose access has expired are logged out immediately
    on their next request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # 1. Check if user is still active
            if not request.user.is_active:
                auth_logout(request)
                messages.error(request, "Your account has been deactivated.")
                return redirect('login')

            # 2. Check if user has a valid Profile (superusers can be profile-less)
            profile = getattr(request.user, 'profile', None)
            if not profile and not request.user.is_superuser:
                auth_logout(request)
                messages.error(request, "Your account has been disconnected from your organization.")
                return redirect('login')

            # 3. Check if access is expired
            if profile and profile.access_expires_on:
                if profile.access_expires_on < timezone.now().date():
                    auth_logout(request)
                    messages.error(request, "Your organization access has expired. Contact your owner.")
                    return redirect('login')

        response = self.get_response(request)
        return response
