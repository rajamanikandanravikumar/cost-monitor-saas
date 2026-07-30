from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('member', 'Member'),
]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    email_verified = models.BooleanField(default=False)
    access_expires_on = models.DateField(null=True, blank=True)

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


class OTP(models.Model):
    PURPOSE_CHOICES = [
        ('verify_email', 'Email verification'),
        ('login', 'Login second factor'),
        ('password_reset', 'Password reset'),
    ]

    MAX_ATTEMPTS = 5
    VALID_MINUTES = 10
    RESEND_COOLDOWN_SECONDS = 60

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        return not self.is_used and self.attempts < self.MAX_ATTEMPTS and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP for {self.user.username} ({self.purpose})"