def can_manage_target(actor_profile, target_profile):
    """
    An admin can manage (remove, set expiry on) any member in their own
    organization. There's exactly one admin per org, so an admin can never
    be a valid target — removing them would leave the org with no admin.
    """
    if actor_profile.organization_id != target_profile.organization_id:
        return False
    if target_profile.role != 'member':
        return False
    if actor_profile.user_id == target_profile.user_id:
        return False
    return actor_profile.role == 'admin'