from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Allows access to users whose role is 'admin' OR 'owner' — owner is a
    superset of admin, not a separate track.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        profile = getattr(request.user, 'profile', None)
        if profile is None or profile.role not in ('admin', 'owner'):
            messages.error(request, "You don't have permission to view that page.")
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    """
    Restricts a view to the org's owner specifically. Used for actions that
    change other people's roles or remove them — deliberately not available
    to plain admins, so a compromised or careless admin account can't
    demote/remove the owner or other admins.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        profile = getattr(request.user, 'profile', None)
        if profile is None or profile.role != 'owner':
            messages.error(request, "Only the organization owner can do that.")
            return redirect('team_panel')

        return view_func(request, *args, **kwargs)
    return wrapper