from django.urls import path
from . import views

urlpatterns = [
    path('team/', views.team_panel_view, name='team_panel'),
    path('team/invite/', views.invite_teammate_view, name='invite_teammate'),
    path('team/remark/<int:user_id>/', views.add_remark_view, name='add_remark'),
    path('team/remove/<int:user_id>/', views.remove_member_view, name='remove_member'),
    path('team/set-expiry/<int:user_id>/', views.set_expiry_view, name='set_expiry'),
]