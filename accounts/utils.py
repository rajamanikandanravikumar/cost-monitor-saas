import secrets
import sys
import logging
import smtplib
import socket
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import OTP

logger = logging.getLogger(__name__)


def generate_otp(user, purpose):
    """
    Fast, synchronous database write for generating OTP.
    Raises ValueError if called within the resend cooldown window.
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
    subject = PURPOSE_SUBJECTS.get(purpose, "Your Cost Monitor code")
    intro = PURPOSE_MESSAGES.get(purpose, "Your code is:")
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)

    print(f" Attempting to send OTP email to {email} from {from_email}...", flush=True)

    try:
        # Django send_mail with error handling to avoid 500 Internal Server Errors
        sent_count = send_mail(
            subject=subject,
            message=(
                f"Hi,\n\n{intro}\n\n    {code}\n\n"
                f"This code expires in {OTP.VALID_MINUTES} minutes and can only be used once.\n"
                f"If you didn't request this, you can safely ignore this email."
            ),
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        print(f" SUCCESS: OTP email sent to {email} (Sent count: {sent_count})", flush=True)
        return True

    except (smtplib.SMTPException, socket.timeout, socket.error, Exception) as e:
        # Prevents crashing the view into a 500 Internal Server Error
        print(f" ERROR: OTP EMAIL FAILED for {email}: {repr(e)}", flush=True)
        logger.error(f"OTP email dispatch failure for {email}: {repr(e)}", exc_info=True)
        return False


def send_otp_for(user, purpose):
    """
    Main entry point: generates the OTP and attempts email dispatch.
    Returns the generated OTP object.
    """
    otp = generate_otp(user, purpose)
    _send_otp_email_now(user.id, user.email, purpose, otp.code)
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