from django.db import models
from django.contrib.auth.models import User

#==========================================================
# VolunteerProfile model to store volunteer-specific information

class VolunteerProfile(models.Model):
    # Har profile ek Django User se judi hogi
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile')
    
    # Category of help (e.g., 'Blood Bank', 'Medical', 'Tech Support')
    service_role = models.CharField(max_length=100) 
    
    # Active/Offline Toggle
    is_available = models.BooleanField(default=True)
    
    # For future distance calculations (Haversine formula)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    location_description = models.CharField(max_length=255, null=True, blank=True)
    

    def __str__(self):
        return f"{self.user.username} - {self.service_role} ({'Online' if self.is_available else 'Offline'})"