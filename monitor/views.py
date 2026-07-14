from django.shortcuts import render
from django.db.models import Sum, Avg
from .models import CostSnapshot

def dashboard(request):
    # 1. Total cost per service (for the chart)
    service_totals = (
        CostSnapshot.objects
        .values('service')
        .annotate(total=Sum('cost_usd'))
        .order_by('-total')
    )

    # 2. Daily totals across all services (for a trend line)
    daily_totals = (
        CostSnapshot.objects
        .values('date')
        .annotate(total=Sum('cost_usd'))
        .order_by('date')
    )
    
    # 3. Aggregate Top Metric KPI Cards (Fixing the $0.00 Bug!)
    total_spend = CostSnapshot.objects.aggregate(total=Sum('cost_usd'))['total'] or 0
    daily_average = CostSnapshot.objects.values('date').annotate(day_total=Sum('cost_usd')).aggregate(avg=Avg('day_total'))['avg'] or 0

    # 4. Recent individual records for the table
    recent_records = CostSnapshot.objects.all().order_by('-date')[:20]

    # 5. Flagged anomalies, most recent first
    anomalies = CostSnapshot.objects.filter(is_anomaly=True).order_by('-date')

    # 6. Pass ALL values securely into the UI context
    context = {
        'service_totals': list(service_totals),
        'daily_totals': list(daily_totals),
        'total_spend': total_spend,          # Added this
        'daily_average': daily_average,      # Added this
        'recent_records': recent_records,
        'anomalies': anomalies,
        'anomaly_count': anomalies.count(),
    }
    return render(request, 'monitor/dashboard.html', context)