from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('internal/run-detection/', views.run_scheduled_detection, name='run_detection'),
]