from django.shortcuts import redirect
from django.contrib import messages

EXEMPT_PREFIXES = ('/accounts/', '/admin/', '/static/')


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile is not None and not profile.email_verified:
                path = request.path
                if path != '/' and not path.startswith(EXEMPT_PREFIXES):
                    messages.error(request, "Please verify your email to continue.")
                    return redirect('verify_otp')

        return self.get_response(request)