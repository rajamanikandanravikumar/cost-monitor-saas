import secrets
import logging
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import OTP

logger = logging.getLogger(__name__)


def generate_otp(user, purpose):
    recent = (
        OTP.objects.filter(user=user, purpose=purpose)
        .order_by("-created_at")
        .first()
    )

    if recent and not recent.is_used:
        seconds_since = (timezone.now() - recent.created_at).total_seconds()

        if seconds_since < OTP.RESEND_COOLDOWN_SECONDS:
            wait = int(OTP.RESEND_COOLDOWN_SECONDS - seconds_since)
            raise ValueError(
                f"Please wait {wait} seconds before requesting another code."
            )

    OTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    code = f"{secrets.randbelow(1000000):06d}"

    otp = OTP.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=timezone.now()
        + timedelta(minutes=OTP.VALID_MINUTES),
    )

    return otp


PURPOSE_SUBJECTS = {
    "verify_email": "Verify your Cost Monitor account",
    "login": "Your Cost Monitor login code",
    "password_reset": "Your Cost Monitor password reset code",
}

PURPOSE_MESSAGES = {
    "verify_email": "Your email verification code is:",
    "login": "Your login verification code is:",
    "password_reset": "Your password reset code is:",
}


def send_otp_email(user, purpose, code):
    subject = PURPOSE_SUBJECTS.get(
        purpose,
        "Your Cost Monitor Code",
    )

    intro = PURPOSE_MESSAGES.get(
        purpose,
        "Your verification code is:",
    )

    body = f"""
Hi,

{intro}

{code}

This code expires in {OTP.VALID_MINUTES} minutes.

If you didn't request this code, simply ignore this email.

Cost Monitor
"""

    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        logger.info(
            "OTP email sent successfully to %s",
            user.email,
        )

    except Exception:
        logger.exception(
            "Failed sending OTP to %s",
            user.email,
        )
        raise


def send_otp_for(user, purpose):
    otp = generate_otp(user, purpose)

    send_otp_email(
        user,
        purpose,
        otp.code,
    )

    return otp


def verify_otp(user, purpose, submitted_code):
    otp = (
        OTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if otp is None:
        return False, "No active code found."

    if timezone.now() >= otp.expires_at:
        return False, "This code has expired."

    if otp.attempts >= OTP.MAX_ATTEMPTS:
        return False, "Too many attempts."

    if submitted_code.strip() != otp.code:
        otp.attempts += 1
        otp.save()

        remaining = OTP.MAX_ATTEMPTS - otp.attempts

        return (
            False,
            f"Incorrect code. {remaining} attempts remaining.",
        )

    otp.is_used = True
    otp.save()

    return True, "Verified."