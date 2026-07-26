from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from .forms import RegisterForm
from .models import Organization, Profile
from .utils import send_verification_email


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            try:
                with transaction.atomic():
                    organization = Organization.objects.create(name=data["organization_name"])

                    user = User.objects.create_user(
                        username=data["username"],
                        email=data["email"],
                        password=data["password"],
                    )

                    Profile.objects.create(
                        user=user, 
                        organization=organization, 
                        role="owner",
                        email_verified=False
                    )

                # Send verification email outside atomic transaction to avoid rolling back email triggers
                send_verification_email(request, user)
                
                messages.success(
                    request, 
                    "Registration successful! Please check your email and click the verification link to activate your account."
                )
                return redirect("login")
            except Exception as e:
                messages.error(request, f"An error occurred during registration: {str(e)}")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile = getattr(user, 'profile', None)

            if profile:
                # 1. Check email verification
                if not profile.email_verified:
                    messages.error(
                        request,
                        "Your email is not verified. Please check your inbox or request a new verification link below."
                    )
                    return render(request, "accounts/login.html", {
                        "form": AuthenticationForm(),
                        "show_resend_link": True
                    })

                # 2. Check access expiry
                if profile.access_expires_on and profile.access_expires_on < timezone.now().date():
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
    if request.method == "POST":
        auth_logout(request)
        return redirect("home")
    # For safety with existing GET logout links, we show a confirmation page
    return render(request, "accounts/logout_confirm.html")


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        profile = getattr(user, 'profile', None)
        if profile:
            profile.email_verified = True
            profile.save()
            messages.success(request, "Thank you! Your email has been successfully verified. You can now log in.")
        else:
            messages.error(request, "No profile found for this user.")
        return redirect("login")
    else:
        messages.error(request, "The verification link is invalid or has expired.")
        return redirect("login")


def resend_verification_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
            profile = getattr(user, 'profile', None)
            if profile:
                if profile.email_verified:
                    messages.info(request, "This email is already verified. Please log in.")
                    return redirect("login")
                
                send_verification_email(request, user)
                messages.success(request, "A new verification link has been sent to your email.")
                return redirect("login")
            else:
                messages.error(request, "No user profile found for this email address.")
        except User.DoesNotExist:
            # We use a generic message to prevent user enumeration
            messages.success(request, "If an account with that email exists, we have sent a verification link.")
            return redirect("login")
            
    return render(request, "accounts/resend_verification.html")
