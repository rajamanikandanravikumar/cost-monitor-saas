from django.db import models
from django.contrib.auth.models import User


class Organization(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='members'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

    # Optional access expiry — if set and in the past, login is blocked.
    # Null means "no expiry, access indefinite."
    access_expires_on = models.DateField(
        null=True, blank=True,
        help_text="If set, this user cannot log in after this date."
    )

    def __str__(self):
        return f"{self.user.username} ({self.organization.name}, {self.role})"


class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        status = "active" if self.logout_time is None else f"ended {self.logout_time}"
        return f"{self.user.username} — {self.login_time} ({status})"