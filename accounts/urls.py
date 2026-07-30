from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/<str:purpose>/', views.resend_otp_view, name='resend_otp'),

    path('login/', views.login_view, name='login'),
    path('login/otp/', views.login_otp_view, name='login_otp'),
    path('login/otp/resend/', views.resend_login_otp_view, name='resend_login_otp'),
    path('logout/', views.logout_view, name='logout'),

    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/resend/', views.resend_reset_otp_view, name='resend_reset_otp'),
]