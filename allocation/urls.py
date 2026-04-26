from django.urls import path
from . import views

urlpatterns = [
    path('request/', views.create_request, name='create_request'),
    path('success/', views.success, name='success'),
    path('match/', views.create_request, name='match_volunteer'),
]