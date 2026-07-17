from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone

from .forms import RegisterForm
from .models import Organization, Profile


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            organization = Organization.objects.create(name=data["organization_name"])

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )

            # The founding user of a new organization is its owner — the
            # protected top role, not a demotable admin.
            Profile.objects.create(user=user, organization=organization, role="owner")

            auth_login(request, user)
            messages.success(request, f"Welcome, {user.username} — your organization has been created.")
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile = getattr(user, 'profile', None)

            # Block login if this user's access has an expiry date that has
            # already passed. Checked here, before auth_login(), so an
            # expired account never gets a valid session at all.
            if (
                profile
                and profile.access_expires_on
                and profile.access_expires_on < timezone.now().date()
            ):
                messages.error(
                    request,
                    "Your access has expired. Contact your organization owner."
                )
                return render(request, "accounts/login.html", {"form": AuthenticationForm()})

            auth_login(request, user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("home")