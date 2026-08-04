import secrets
import threading
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail

from .models import OTP


def generate_otp(user, purpose):
    """
    Fast, synchronous — just database writes. Raises ValueError if called
    within the resend cooldown window.
    """
    recent = OTP.objects.filter(user=user, purpose=purpose).order_by('-created_at').first()
    if recent and not recent.is_used:
        seconds_since = (timezone.now() - recent.created_at).total_seconds()
        if seconds_since < OTP.RESEND_COOLDOWN_SECONDS:
            wait = int(OTP.RESEND_COOLDOWN_SECONDS - seconds_since)
            raise ValueError(f"Please wait {wait} seconds before requesting another code.")

    OTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

    code = f"{secrets.randbelow(1000000):06d}"
    otp = OTP.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP.VALID_MINUTES),
    )
    return otp


PURPOSE_SUBJECTS = {
    'verify_email': "Verify your Cost Monitor account",
    'login': "Your Cost Monitor login code",
    'password_reset': "Your Cost Monitor password reset code",
}

PURPOSE_MESSAGES = {
    'verify_email': "Your email verification code is:",
    'login': "Your login verification code is:",
    'password_reset': "Your password reset code is:",
}


def _send_otp_email_now(user_id, email, purpose, code):
    """
    Runs inside the background thread. Takes plain values (not model
    instances) rather than the user/otp objects themselves — safer across
    a thread boundary, avoids any risk of touching a DB connection that
    belongs to the main request thread.
    """
    subject = PURPOSE_SUBJECTS.get(purpose, "Your Cost Monitor code")
    intro = PURPOSE_MESSAGES.get(purpose, "Your code is:")
    try:
        send_mail(
            subject=subject,
            message=(
                f"Hi,\n\n{intro}\n\n    {code}\n\n"
                f"This code expires in {OTP.VALID_MINUTES} minutes and can only be used once.\n"
                f"If you didn't request this, you can safely ignore this email."
            ),
            from_email=None,
            recipient_list=[email],
            fail_silently=True,  # a background thread has nowhere to surface an error to the user anyway
        )
    except Exception:
        pass  # logged as a future improvement — see PRODUCTION_PLAN.md error monitoring item


def send_otp_for(user, purpose):
    """
    The main entry point views should call: generates the OTP synchronously
    (fast — just a DB write, so cooldown errors still surface immediately),
    then fires the actual email send in a background thread so the HTTP
    response doesn't wait on Gmail's SMTP round-trip.
    """
    otp = generate_otp(user, purpose)  # raises ValueError on cooldown — let the caller handle it

    thread = threading.Thread(
        target=_send_otp_email_now,
        args=(user.id, user.email, purpose, otp.code),
        daemon=True,
    )
    thread.start()

    return otp


def verify_otp(user, purpose, submitted_code):
    otp = OTP.objects.filter(user=user, purpose=purpose, is_used=False).order_by('-created_at').first()

    if otp is None:
        return False, "No active code found. Request a new one."

    if timezone.now() >= otp.expires_at:
        return False, "This code has expired. Request a new one."

    if otp.attempts >= OTP.MAX_ATTEMPTS:
        return False, "Too many incorrect attempts. Request a new one."

    if submitted_code.strip() != otp.code:
        otp.attempts += 1
        otp.save()
        remaining = OTP.MAX_ATTEMPTS - otp.attempts
        return False, f"Incorrect code. {remaining} attempt(s) remaining."

    otp.is_used = True
    otp.save()
    return True, "Verified."