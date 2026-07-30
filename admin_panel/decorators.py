from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Restricts a view to the org's admin — the single, permanent admin set
    at registration. There is no separate 'owner' tier per-org anymore;
    the platform Owner is the superuser account, handled separately via
    @staff_member_required in core/views.py.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        profile = getattr(request.user, 'profile', None)
        if profile is None or profile.role != 'admin':
            messages.error(request, "You don't have permission to view that page.")
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper