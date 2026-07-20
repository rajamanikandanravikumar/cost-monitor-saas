from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('thread/<int:user_id>/', views.thread_view, name='thread'),
]