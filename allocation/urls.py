from django.urls import path
from . import views

urlpatterns = [
    # Auth URLs
    path('register/', views.register_user, name='user_register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('user_profile/', views.user_profile, name='user_profile'),
    #path('request_help/', views.create_request, name='create_request')
    # Core Flow URLs (activeted)
    path('role-selection/', views.role_selection, name='role_selection'),
    path('request-help/', views.create_request, name='create_request'),
    path('match/<int:request_id>/', views.find_volunteers, name='find_volunteers'),
    path('select/<int:request_id>/<int:volunteer_id>/', views.select_volunteer, name='select_volunteer'),
    path('track/<int:request_id>/', views.track_request, name='track_request'),
]