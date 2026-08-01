from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone

from .forms import RegisterForm
from .models import Organization, Profile
from .utils import send_otp_for, verify_otp


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
                send_otp_for(user, "verify_email")
            except ValueError:
                pass  # cooldown can't realistically trigger on a brand new user — ignore defensively

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

    if request.method == "POST":
        code = request.POST.get("code", "")
        success, message = verify_otp(request.user, "verify_email", code)
        if success:
            if profile:
                profile.email_verified = True
                profile.save()
            messages.success(request, "Email verified!")
            return redirect("dashboard")
        else:
            messages.error(request, message)

    return render(request, "accounts/resend_verification.html")


def resend_otp_view(request, purpose):
    if request.method != "POST" or not request.user.is_authenticated:
        return redirect("verify_otp")

    try:
        send_otp_for(request.user, purpose)
        messages.success(request, "A new code has been sent.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("verify_otp" if purpose == "verify_email" else "login")


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
            messages.error(request, "Your access has expired. Contact your organization admin.")
            return render(request, "accounts/login.html")

        try:
            send_otp_for(user, "login")
        except ValueError as e:
            messages.error(request, str(e))
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
        del request.session['pending_login_user_id']
        return redirect("login")

    if request.method == "POST":
        code = request.POST.get("code", "")
        success, message = verify_otp(user, "login", code)
        if success:
            del request.session['pending_login_user_id']
            auth_login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, message)

    return render(request, "accounts/login_otp.html", {"email": user.email})


def resend_login_otp_view(request):
    if request.method != "POST":
        return redirect("login")

    pending_id = request.session.get('pending_login_user_id')
    if not pending_id:
        return redirect("login")

    try:
        user = User.objects.get(pk=pending_id)
        send_otp_for(user, "login")
        messages.success(request, "A new code has been sent.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("login_otp")


def password_reset_request_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        user = User.objects.filter(email=email).first()

        if user:
            try:
                send_otp_for(user, "password_reset")
                request.session['pending_reset_user_id'] = user.pk
            except ValueError:
                pass

        messages.success(request, "If that email is registered, a reset code has been sent.")
        return redirect("password_reset_confirm")

    return render(request, "accounts/password_reset_form.html")


def password_reset_confirm_view(request):
    pending_id = request.session.get('pending_reset_user_id')

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
            return render(request, "accounts/password_reset_confirm.html")

        try:
            validate_password(password1, user=user)
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
            return render(request, "accounts/password_reset_confirm.html")

        success, message = verify_otp(user, "password_reset", code)
        if not success:
            messages.error(request, message)
            return render(request, "accounts/password_reset_confirm.html")

        user.set_password(password1)
        user.save()
        del request.session['pending_reset_user_id']

        messages.success(request, "Password updated — you can now log in.")
        return redirect("login")

    return render(request, "accounts/password_reset_confirm.html")


def resend_reset_otp_view(request):
    if request.method != "POST":
        return redirect("password_reset_confirm")

    pending_id = request.session.get('pending_reset_user_id')
    if not pending_id:
        return redirect("password_reset_request")

    try:
        user = User.objects.get(pk=pending_id)
        send_otp_for(user, "password_reset")
        messages.success(request, "A new code has been sent.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("password_reset_confirm")


def logout_view(request):
    auth_logout(request)
    return redirect("home")