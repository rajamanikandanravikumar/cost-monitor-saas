import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail

from .models import OTP


def generate_otp(user, purpose):
    """
    Invalidates any prior unused OTPs of this purpose for this user, then
    creates and returns a fresh one. Enforces a resend cooldown — raises
    ValueError if called too soon after the last code for this purpose.
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


def send_otp_email(user, otp):
    subject = PURPOSE_SUBJECTS.get(otp.purpose, "Your Cost Monitor code")
    intro = PURPOSE_MESSAGES.get(otp.purpose, "Your code is:")

    send_mail(
        subject=subject,
        message=(
            f"Hi {user.username},\n\n"
            f"{intro}\n\n"
            f"    {otp.code}\n\n"
            f"This code expires in {OTP.VALID_MINUTES} minutes and can only be used once.\n"
            f"If you didn't request this, you can safely ignore this email."
        ),
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


def verify_otp(user, purpose, submitted_code):
    """
    Returns (success: bool, message: str). Increments attempts on failure,
    so a brute-force attempt burns through MAX_ATTEMPTS quickly and locks
    the code, requiring a resend rather than allowing unlimited guesses.
    """
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