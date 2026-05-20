from django.urls import path
from . import views

urlpatterns = [
    # Profile Setup
    path('setup-profile/', views.register_volunteer, name='register_volunteer'),
    
    # Dashboard
    path('dashboard/', views.volunteer_dashboard, name='volunteer_dashboard'),
    
    # Request Actions
    #path('detail/<int:request_id>/', views.request_detail, name='request_detail'),
    path('accept/<int:request_id>/', views.accept_request, name='accept_request'),
    path('decline/<int:request_id>/', views.decline_request, name='decline_request'), # 🔥 NAYA ADD KIYA
    path('mark-done/<int:request_id>/', views.mark_done, name='mark_done'),
    
    # Toggle Online/Offline
    path('toggle-status/', views.toggle_availability, name='toggle_availability'), # 🔥 NAYA ADD KIYA
    
    # My Profile and Requests
    path('my-profile/', views.volunteer_profile, name='volunteer_profile'),
]