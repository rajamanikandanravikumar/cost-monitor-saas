from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.contrib import messages
from django.utils import timezone # Added for timezone aware comparison
from datetime import datetime # Added for baseline datetime initialization

from accounts.models import Profile
from .models import Message
from .permissions import can_message, get_contacts


@login_required
def inbox_view(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, "Messaging isn't available for this account.")
        return redirect('dashboard')

    contacts = get_contacts(profile)

    contact_data = []
    for contact_profile in contacts:
        other_user = contact_profile.user
        last_message = (
            Message.objects
            .filter(
                Q(sender=request.user, recipient=other_user) |
                Q(sender=other_user, recipient=request.user)
            )
            .order_by('-created_at')
            .first()
        )
        unread_count = Message.objects.filter(
            sender=other_user, recipient=request.user, is_read=False
        ).count()

        contact_data.append({
            'profile': contact_profile,
            'user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    # FIXED: Replaced string fallback '' with a timezone-aware datetime baseline
    contact_data.sort(
        key=lambda c: c['last_message'].created_at if c['last_message'] else timezone.make_aware(datetime.min),
        reverse=True
    )

    context = {
        'organization': profile.organization,
        'contact_data': contact_data,
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def thread_view(request, user_id):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        messages.error(request, "Messaging isn't available for this account.")
        return redirect('dashboard')

    other_user = get_object_or_404(User, id=user_id)
    other_profile = get_object_or_404(Profile, user=other_user)

    if not can_message(profile, other_profile):
        messages.error(request, "You can't message that user.")
        return redirect('inbox')

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(
                organization=profile.organization,
                sender=request.user,
                recipient=other_user,
                body=body,
            )
        return redirect('thread', user_id=user_id)

    # Mark incoming messages from this contact as read
    Message.objects.filter(
        sender=other_user, recipient=request.user, is_read=False
    ).update(is_read=True)

    conversation = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('created_at')

    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'conversation': conversation,
    }
    return render(request, 'messaging/thread.html', context)