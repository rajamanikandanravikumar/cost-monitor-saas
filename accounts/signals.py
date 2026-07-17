from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LoginLog


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginLog.objects.create(
        user=user,
        ip_address=get_client_ip(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is None:
        return
    open_log = (
        LoginLog.objects
        .filter(user=user, logout_time__isnull=True)
        .order_by('-login_time')
        .first()
    )
    if open_log:
        from django.utils import timezone
        open_log.logout_time = timezone.now()
        open_log.save()