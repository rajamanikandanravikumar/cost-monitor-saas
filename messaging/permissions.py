def can_message(profile_a, profile_b):
    """
    Two people can message each other only if:
    - They're in the same organization (never cross-org)
    - Their roles are different (hierarchical channel: member<->admin,
      member<->owner, admin<->owner — not member<->member or admin<->admin)
    - They're not the same person
    """
    if profile_a.organization_id != profile_b.organization_id:
        return False
    if profile_a.user_id == profile_b.user_id:
        return False
    if profile_a.role == profile_b.role:
        return False
    return True


def get_contacts(profile):
    """
    Returns the queryset of Profiles that this profile is allowed to
    message — i.e. everyone in their org with a different role.
    """
    from accounts.models import Profile
    return (
        Profile.objects
        .filter(organization=profile.organization)
        .exclude(user=profile.user)
        .exclude(role=profile.role)
        .select_related('user')
    )