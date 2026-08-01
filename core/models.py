from django.db import models
from django.contrib.auth.models import User
from accounts.models import Organization


class PlatformMessage(models.Model):
    """
    A private channel between the platform operator (superuser) and one
    organization's admin. Deliberately a separate model from messaging.Message
    so this can never be confused with, or accidentally weaken, the
    same-organization-only rule that regular messaging enforces.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='platform_messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='platform_messages_sent')
    is_from_platform = models.BooleanField(default=False)  # True = superuser sent it, False = org admin sent it
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        who = "Platform" if self.is_from_platform else self.organization.name
        return f"{who}: {self.body[:30]}"