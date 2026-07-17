from django.db import models
from django.contrib.auth.models import User
from accounts.models import Organization


class Remark(models.Model):
    """
    An admin-written note about a specific user within their organization.
    Scoped to organization as well as user, so a remark can never be
    displayed to or written by anyone outside the organization it belongs to.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    target_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='remarks_received'
    )
    written_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='remarks_written'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Remark on {self.target_user.username} by {self.written_by}"