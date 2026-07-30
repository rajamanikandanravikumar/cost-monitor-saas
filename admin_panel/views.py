from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from datetime import datetime

from accounts.models import Profile, LoginLog
from .decorators import admin_required
from .permissions import can_manage_target
from .models import Remark


@login_required
@admin_required
def team_panel_view(request):
    org = request.user.profile.organization
    viewer_profile = request.user.profile

    profiles = (
        Profile.objects
        .filter(organization=org)
        .select_related('user')
        .order_by('user__username')
    )

    team_data = []
    for profile in profiles:
        user = profile.user
        recent_logins = LoginLog.objects.filter(user=user)[:5]
        remarks = Remark.objects.filter(organization=org, target_user=user)[:5]
        team_data.append({
            'profile': profile,
            'user': user,
            'recent_logins': recent_logins,
            'remarks': remarks,
            'can_manage': can_manage_target(viewer_profile, profile),
        })

    context = {
        'organization': org,
        'team_data': team_data,
    }
    return render(request, 'admin_panel/team_panel.html', context)


@login_required
@admin_required
def invite_teammate_view(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('team_panel')

    org = request.user.profile.organization

    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")

    error = None
    if not username or not email or not password:
        error = "All fields are required."
    elif User.objects.filter(username=username).exists():
        error = "That username is already taken."
    elif User.objects.filter(email=email).exists():
        error = "That email is already registered to another account."
    else:
        try:
            validate_password(password)
        except ValidationError as e:
            error = " ".join(e.messages)

    if error:
        messages.error(request, error)
    else:
        new_user = User.objects.create_user(
            username=username, email=email, password=password
        )
        # Invited teammates are always members — there is exactly one
        # admin per org, set at registration, never assigned here.
        Profile.objects.create(user=new_user, organization=org, role="member")
        messages.success(request, f"{username} has been added to {org.name}.")

    return redirect('team_panel')


@login_required
@admin_required
def add_remark_view(request, user_id):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('team_panel')

    org = request.user.profile.organization
    target_profile = get_object_or_404(Profile, user_id=user_id, organization=org)
    target_user = target_profile.user

    text = request.POST.get("text", "").strip()
    if text:
        Remark.objects.create(
            organization=org,
            target_user=target_user,
            written_by=request.user,
            text=text,
        )
        messages.success(request, f"Remark added for {target_user.username}.")
    else:
        messages.error(request, "Remark text cannot be empty.")

    return redirect('team_panel')


@login_required
@admin_required
def remove_member_view(request, user_id):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('team_panel')

    org = request.user.profile.organization
    target_profile = get_object_or_404(Profile, user_id=user_id, organization=org)

    if not can_manage_target(request.user.profile, target_profile):
        messages.error(request, "You don't have permission to remove that user.")
        return redirect('team_panel')

    target_user = target_profile.user
    target_user.is_active = False
    target_user.save()
    target_profile.delete()

    messages.success(request, f"{target_user.username} has been removed from {org.name}.")
    return redirect('team_panel')


@login_required
@admin_required
def set_expiry_view(request, user_id):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect('team_panel')

    org = request.user.profile.organization
    target_profile = get_object_or_404(Profile, user_id=user_id, organization=org)

    if not can_manage_target(request.user.profile, target_profile):
        messages.error(request, "You don't have permission to change that user's access.")
        return redirect('team_panel')

    date_str = request.POST.get("expires_on", "").strip()
    if date_str:
        try:
            target_profile.access_expires_on = datetime.strptime(date_str, "%Y-%m-%d").date()
            target_profile.save()
            messages.success(request, f"{target_profile.user.username}'s access now expires on {date_str}.")
        except ValueError:
            messages.error(request, "Invalid date format.")
    else:
        target_profile.access_expires_on = None
        target_profile.save()
        messages.success(request, f"Expiry cleared for {target_profile.user.username}.")

    return redirect('team_panel')