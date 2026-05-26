from django.db import models
from django.contrib.auth.models import User
from volunteer.models import VolunteerProfile

class HelpRequest(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    
    # 🔥 FIX: show status on user screen 
    STATUS_CHOICES = [
        ('Pending', 'Pending'),        # Step 1: User form submited
        ('Selected', 'Selected'),      # Step 2: User selectected someone
        ('Assigned', 'Assigned'),      # Step 3: Volunteer incoming lists
        ('Accepted', 'Accepted'),      # Step 4: Volunteer pressed Accept  (Lock Opens)
        ('Completed', 'Completed'),    # Step 5: Mission Accomplished
    ]

    #add these two fields to track the location and contact details of the requester
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # user specific details for the request
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_requests')
    
    # Problem category (e.g., 'Blood Bank', 'Medical', 'Tech Support')
    problem_category = models.CharField(max_length=100) 
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # 🔥 logic for contact
    location = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    # ==========================================
    # 🔒 PRIVACY LOCK: this field id is lock when volunteer accepts the request then show all details
    private_details = models.TextField(help_text="Encrypted: Extra instructions, exact situation.", null=True, blank=True)
    # ==========================================
    
    # save details of assigned volunteer (agar assigned hai to)
    target_volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    declined_by = models.ManyToManyField(VolunteerProfile, blank=True, related_name='declined_requests')
    status_message = models.CharField(max_length=255, null=True, blank=True)  # Optional field for status updates or messages
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.priority}] {self.problem_category} - by {self.requester.username}"