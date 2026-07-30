import time
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone

from .forms import RegisterForm
from .models import Organization, Profile
from .utils import generate_otp, send_otp_email, verify_otp

OTP_EXPIRY_SECONDS = 120  # 2 Minutes Countdown Duration


def _get_otp_seconds_remaining(request):
    """Calculates remaining seconds before the active OTP session expires."""
    created_at = request.session.get('otp_created_at')
    if not created_at:
        return 0
    elapsed = int(time.time() - created_at)
    return max(0, OTP_EXPIRY_SECONDS - elapsed)


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            if User.objects.filter(email=data["email"]).exists():
                form.add_error("email", "That email is already registered.")
                return render(request, "accounts/register.html", {"form": form})

            organization = Organization.objects.create(name=data["organization_name"])
            user = User.objects.create_user(
                username=data["username"], email=data["email"], password=data["password"]
            )
            Profile.objects.create(user=user, organization=organization, role="admin")

            try:
                otp = generate_otp(user, "verify_email")
                send_otp_email(user, otp)
                request.session['otp_created_at'] = time.time()
            except Exception:
                messages.warning(request, "Account created, but we couldn't send a verification code. Try resending it.")

            auth_login(request, user)
            messages.success(request, f"Enter the 6-digit code sent to {user.email}.")
            return redirect("verify_otp")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def verify_otp_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    profile = getattr(request.user, 'profile', None)
    if profile and profile.email_verified:
        return redirect("dashboard")

    seconds_remaining = _get_otp_seconds_remaining(request)

    if request.method == "POST":
        code = request.POST.get("code", "")
        success, message = verify_otp(request.user, "verify_email", code)
        if success:
            if profile:
                profile.email_verified = True
                profile.save()
            request.session.pop('otp_created_at', None)
            messages.success(request, "Email verified!")
            return redirect("dashboard")
        else:
            messages.error(request, message)

    return render(request, "accounts/resend_verification.html", {
        "purpose": "verify_email",
        "otp_seconds_remaining": seconds_remaining,
        "show_resend_link": seconds_remaining == 0,
    })


def resend_otp_view(request, purpose):
    if request.method != "POST":
        return redirect("verify_otp")

    if not request.user.is_authenticated:
        return redirect("login")

    try:
        otp = generate_otp(request.user, purpose)
        send_otp_email(request.user, otp)
        request.session['otp_created_at'] = time.time()
        messages.success(request, "A new code has been sent.")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception:
        messages.error(request, "Couldn't send the code right now — try again shortly.")

    if purpose == "verify_email":
        return redirect("verify_otp")
    return redirect("login")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Incorrect username or password.")
            return render(request, "accounts/login.html")

        profile = getattr(user, 'profile', None)
        if (
            profile
            and profile.access_expires_on
            and profile.access_expires_on < timezone.now().date()
        ):
            messages.error(request, "Your access has expired. Contact your organization owner.")
            return render(request, "accounts/login.html")

        try:
            otp = generate_otp(user, "login")
            send_otp_email(user, otp)
            request.session['otp_created_at'] = time.time()
        except Exception:
            messages.error(request, "Couldn't send a login code right now — try again shortly.")
            return render(request, "accounts/login.html")

        request.session['pending_login_user_id'] = user.pk
        messages.success(request, f"Enter the code sent to {user.email}.")
        return redirect("login_otp")

    return render(request, "accounts/login.html")


def login_otp_view(request):
    pending_id = request.session.get('pending_login_user_id')
    if not pending_id:
        return redirect("login")

    try:
        user = User.objects.get(pk=pending_id)
    except User.DoesNotExist:
        request.session.pop('pending_login_user_id', None)
        return redirect("login")

    seconds_remaining = _get_otp_seconds_remaining(request)

    if request.method == "POST":
        code = request.POST.get("code", "")
        success, message = verify_otp(user, "login", code)
        if success:
            request.session.pop('pending_login_user_id', None)
            request.session.pop('otp_created_at', None)
            auth_login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, message)

    return render(request, "accounts/login_otp.html", {
        "email": user.email,
        "otp_seconds_remaining": seconds_remaining,
        "show_resend_link": seconds_remaining == 0,
    })


def resend_login_otp_view(request):
    if request.method != "POST":
        return redirect("login")

    pending_id = request.session.get('pending_login_user_id')
    if not pending_id:
        return redirect("login")

    try:
        user = User.objects.get(pk=pending_id)
        otp = generate_otp(user, "login")
        send_otp_email(user, otp)
        request.session['otp_created_at'] = time.time()
        messages.success(request, "A new code has been sent.")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception:
        messages.error(request, "Couldn't send the code right now.")

    return redirect("login_otp")


def password_reset_request_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        user = User.objects.filter(email=email).first()

        if user:
            try:
                otp = generate_otp(user, "password_reset")
                send_otp_email(user, otp)
                request.session['pending_reset_user_id'] = user.pk
                request.session['otp_created_at'] = time.time()
            except Exception:
                pass

        messages.success(request, "If that email is registered, a reset code has been sent.")
        return redirect("password_reset_confirm")

    return render(request, "accounts/password_reset_form.html")


def password_reset_confirm_view(request):
    pending_id = request.session.get('pending_reset_user_id')

    if not pending_id and request.method != "POST":
        messages.error(request, "Request a reset code first.")
        return redirect("password_reset_request")

    seconds_remaining = _get_otp_seconds_remaining(request)

    if request.method == "POST":
        if not pending_id:
            messages.error(request, "Request a reset code first.")
            return redirect("password_reset_request")

        try:
            user = User.objects.get(pk=pending_id)
        except User.DoesNotExist:
            return redirect("password_reset_request")

        code = request.POST.get("code", "")
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/password_reset_confirm.html", {
                "otp_seconds_remaining": seconds_remaining,
                "show_resend_link": seconds_remaining == 0,
            })

        try:
            validate_password(password1, user=user)
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
            return render(request, "accounts/password_reset_confirm.html", {
                "otp_seconds_remaining": seconds_remaining,
                "show_resend_link": seconds_remaining == 0,
            })

        success, message = verify_otp(user, "password_reset", code)
        if not success:
            messages.error(request, message)
            return render(request, "accounts/password_reset_confirm.html", {
                "otp_seconds_remaining": seconds_remaining,
                "show_resend_link": seconds_remaining == 0,
            })

        user.set_password(password1)
        user.save()
        request.session.pop('pending_reset_user_id', None)
        request.session.pop('otp_created_at', None)

        messages.success(request, "Password updated — you can now log in.")
        return redirect("login")

    return render(request, "accounts/password_reset_confirm.html", {
        "otp_seconds_remaining": seconds_remaining,
        "show_resend_link": seconds_remaining == 0,
    })


def resend_reset_otp_view(request):
    if request.method != "POST":
        return redirect("password_reset_confirm")

    pending_id = request.session.get('pending_reset_user_id')
    if not pending_id:
        return redirect("password_reset_request")

    try:
        user = User.objects.get(pk=pending_id)
        otp = generate_otp(user, "password_reset")
        send_otp_email(user, otp)
        request.session['otp_created_at'] = time.time()
        messages.success(request, "A new code has been sent.")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception:
        messages.error(request, "Couldn't send the code right now.")

    return redirect("password_reset_confirm")


def logout_view(request):
    auth_logout(request)
    return redirect("home")