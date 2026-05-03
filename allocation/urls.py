from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('request/', views.create_request, name='create_request'),
    path('success/', views.success, name='success'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    path('register/', views.register, name='register'),
    
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html'
    ), name='login'),

    path('role-selection/', views.role_selection, name='role_selection'),
]