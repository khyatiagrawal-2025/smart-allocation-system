from django.urls import path
from . import views

urlpatterns = [
    path('profile/',              views.volunteer_profile, name='volunteer_profile'),
    path('requests/',             views.request_list,      name='request_list'),
    path('requests/<int:pk>/',    views.request_detail,    name='request_detail'),
    path('requests/<int:pk>/accept/',  views.accept_request,  name='accept_request'),
    path('requests/<int:pk>/cancel/',  views.cancel_request,  name='cancel_request'),
    path('requests/<int:pk>/resolve/', views.resolve_request, name='resolve_request'),
    path('requests/<int:pk>/assign/',  views.assign_request,  name='assign_request'),
    path('dashboard/', views.volunteer_dashboard, name='volunteer_dashboard'),
]