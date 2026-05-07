from django.db import models
from django.contrib.auth.models import User
from volunteer.models import VolunteerProfile # Link to the volunteer app

class HelpRequest(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),        # Step 1: User ne form submit kiya
        ('Selected', 'Selected'),      # Step 2: User ne kisi volunteer ko select kiya
        ('Accepted', 'Accepted'),      # Step 3: Volunteer ne Accept dabaya (Lock Opens)
        ('Resolved', 'Resolved'),      # Step 4: Mission Accomplished
    ]

    # Kis user ne help maangi hai
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_requests')
    
    # Match engine ke liye category
    problem_category = models.CharField(max_length=100) 
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # ==========================================
    # 🔒 PRIVACY LOCK: Yeh text field frontend par tab tak hide rahegi jab tak status 'Accepted' na ho
    private_details = models.TextField(help_text="Encrypted: Phone number, exact address, private instructions.")
    # ==========================================
    
    # Jab user volunteer select karega, toh uski ID yahan save hogi
    target_volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.priority}] {self.problem_category} - by {self.requester.username}"