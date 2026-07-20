from django.db import models
from django.contrib.auth.models import User
from accounts.models import Organization



class Message(models.Model):
    """
    A single private message between two users in the same organization.
    A 'thread' between two people is simply every Message where those two
    users appear as sender/recipient in either direction — there's no
    separate Thread model, since deriving it from Message keeps things
    simple and avoids an extra layer to keep in sync.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.body[:30]}"