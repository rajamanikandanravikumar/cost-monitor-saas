from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('platform-console/', views.platform_console_view, name='platform_console'),
]