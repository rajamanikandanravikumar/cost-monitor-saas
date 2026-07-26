from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

def send_verification_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Construct base link using settings.DASHBOARD_URL to support both local and Render envs
    base_url = settings.DASHBOARD_URL.rstrip('/')
    verification_link = f"{base_url}/accounts/verify/{uid}/{token}/"
    
    context = {
        'user': user,
        'verification_link': verification_link,
    }
    
    subject = "Verify your email address — Cost Monitor"
    message_text = f"Hi {user.username},\n\nPlease verify your email address by clicking the link below:\n{verification_link}\n\nThank you!\nCost Monitor Team"
    
    # Render HTML version too if we want, but simple text is extremely robust
    try:
        send_mail(
            subject,
            message_text,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # We can log this if we have a logger, or let it raise unless handled.
        # But letting it fail is better for visibility unless we want fallback.
        raise e
