from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Avg
from .models import CostSnapshot
import os
from django.http import HttpResponse, HttpResponseForbidden
from django.core.management import call_command
@login_required
def dashboard(request):
    org = request.user.profile.organization

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

    context = {
        'organization': org,
        'service_totals': list(service_totals),
        'daily_totals': list(daily_totals),
        'recent_records': recent_records,
        'anomalies': anomalies,
        'anomaly_count': anomalies.count(),
        'total_spend': total_spend,
        'daily_average': daily_average,
    }
    return render(request, 'monitor/dashboard.html', context)

def run_scheduled_detection(request):
    token = request.GET.get('token')
    expected_token = os.getenv('CRON_SECRET_TOKEN')

    if not expected_token or token != expected_token:
        return HttpResponseForbidden("Forbidden")

    call_command('detect_anomalies')
    return HttpResponse("Detection run complete.")