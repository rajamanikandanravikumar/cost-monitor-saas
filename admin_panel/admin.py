from django.contrib import admin
from .models import Remark


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    list_display = ('target_user', 'organization', 'written_by', 'created_at')
    list_filter = ('organization',)