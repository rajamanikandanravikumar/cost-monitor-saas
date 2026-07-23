from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.core.management import call_command
import os

from .models import CostSnapshot


@login_required
def dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(
            request,
            "This account isn't linked to an organization. "
            "If you're the platform administrator, use /admin/ instead."
        )
        return redirect('home')

    org = profile.organization

    org_records = CostSnapshot.objects.filter(organization=org)

    service_totals = (
        org_records
        .values('service')
        .annotate(total=Sum('cost_usd'))
        .order_by('-total')
    )

    daily_totals = (
        org_records
        .values('date')
        .annotate(total=Sum('cost_usd'))
        .order_by('date')
    )

    recent_records = org_records.order_by('-date')[:20]
    anomalies = org_records.filter(is_anomaly=True).order_by('-date')

    total_spend = org_records.aggregate(total=Sum('cost_usd'))['total'] or 0
    daily_average = (
        org_records
        .values('date')
        .annotate(day_total=Sum('cost_usd'))
        .aggregate(avg=Avg('day_total'))['avg']
        or 0
    )

    from messaging.models import Message
    unread_message_count = Message.objects.filter(recipient=request.user, is_read=False).count()

    context = {
        'organization': org,
        'service_totals': list(service_totals),
        'daily_totals': list(daily_totals),
        'recent_records': recent_records,
        'anomalies': anomalies,
        'anomaly_count': anomalies.count(),
        'total_spend': total_spend,
        'daily_average': daily_average,
        'unread_message_count': unread_message_count,
    }
    return render(request, 'monitor/dashboard.html', context)


def run_scheduled_detection(request):
    """
    Token-protected endpoint, triggered externally (cron-job.org) once a
    day, since django-crontab can't run reliably on Render's free tier
    (the container spins down and takes the OS cron daemon with it).
    """
    token = request.GET.get('token')
    expected_token = os.getenv('CRON_SECRET_TOKEN')

    if not expected_token or token != expected_token:
        return HttpResponseForbidden("Forbidden")

    call_command('detect_anomalies')
    return HttpResponse("Detection run complete.")