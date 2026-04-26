from django.db import models
from django.contrib.auth.models import User

# Volunteer Profile
class Volunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.TextField()
    location = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username


# Request Model
class Request(models.Model):
    URGENCY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=100)
    description = models.TextField()
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES)
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"{self.request_type} - {self.urgency}"


# Allocation Model
class Allocation(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    score = models.IntegerField()
    ecosystem_level = models.CharField(max_length=20)  # local / city / global

    def __str__(self):
        return f"{self.request} -> {self.volunteer}"