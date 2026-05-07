from django.urls import path
from . import views

urlpatterns = [
    path('setup-profile/', views.register_volunteer, name='register_volunteer'),
    path('dashboard/', views.volunteer_dashboard, name='volunteer_dashboard'),
    
    path('detail/<int:request_id>/', views.request_detail, name='request_detail'),
    path('accept/<int:request_id>/', views.accept_request, name='accept_request'),
    path('mission-active/<int:request_id>/', views.resolve_mission, name='resolve_mission'),
    path('mark-done/<int:request_id>/', views.mark_done, name='mark_done'),
    
    path('my-profile/', views.volunteer_profile, name='volunteer_profile'),
]