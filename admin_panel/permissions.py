def can_manage_target(actor_profile, target_profile):
    """
    Determines whether actor_profile is allowed to take an action
    (remove, set expiry) on target_profile.

    Rules:
    - Nobody can act on the owner.
    - Nobody can act on themselves through this path (self-lockout guard).
    - The owner can manage anyone else (admins and members).
    - An admin can only manage members — not other admins, not the owner.
      This keeps offboarding a departing employee (a member) easy for any
      admin, while keeping bigger trust decisions (demoting/removing a
      fellow admin) restricted to the owner.
    """
    if target_profile.role == 'owner':
        return False
    if actor_profile.user_id == target_profile.user_id:
        return False
    if actor_profile.role == 'owner':
        return True
    if actor_profile.role == 'admin':
        return target_profile.role == 'member'
    return False