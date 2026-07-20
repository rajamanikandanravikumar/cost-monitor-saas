from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('messages/', include('messaging.urls')),
    path('', include('core.urls')),
    path('', include('monitor.urls')),
]