from django.urls import path
from . import views

urlpatterns = [
    # Auth URLs
    path('register/', views.register_user, name='user_register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('forgot-password/',   views.forgot_password,   name='forgot_password'),
    path('fp/send-otp/',       views.fp_send_otp,       name='fp_send_otp'),
    path('fp/verify-otp/',     views.fp_verify_otp,     name='fp_verify_otp'),
    path('fp/reset-password/', views.fp_reset_password, name='fp_reset_password'),
    
    # Core Flow URLs (Ab yeh active hain!)
    path('role-selection/', views.role_selection, name='role_selection'),
    path('request-help/', views.create_request, name='create_request'),
    path('match/<int:request_id>/', views.find_volunteers, name='find_volunteers'),
    path('select/<int:request_id>/<int:volunteer_id>/', views.select_volunteer, name='select_volunteer'),
    path('track/<int:request_id>/', views.track_request, name='track_request'),
]