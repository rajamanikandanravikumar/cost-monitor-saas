from django.shortcuts import render


def home_view(request):
    return render(request, "core/home.html")
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from accounts.models import Organization, Profile


@staff_member_required
def platform_console_view(request):
    """
    Restricted via @staff_member_required — only Django staff/superuser
    accounts can reach this, never a regular org's owner/admin/member.
    This is deliberate: one customer organization must never see another's
    name, size, or existence.
    """
    orgs = Organization.objects.all().order_by('-created_at')

    org_data = []
    for org in orgs:
        member_count = Profile.objects.filter(organization=org).count()
        owner_profile = Profile.objects.filter(organization=org, role='owner').first()
        org_data.append({
            'organization': org,
            'member_count': member_count,
            'owner': owner_profile.user if owner_profile else None,
        })

    return render(request, 'core/platform_console.html', {'org_data': org_data})
