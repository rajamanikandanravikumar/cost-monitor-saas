from django.contrib import admin
from .models import Organization, Profile, LoginLog

admin.site.register(Organization)
admin.site.register(Profile)
admin.site.register(LoginLog)