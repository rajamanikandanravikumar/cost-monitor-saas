from django.contrib import admin

# Register your models here.

from .models import CostSnapshot

admin.site.register(CostSnapshot)
