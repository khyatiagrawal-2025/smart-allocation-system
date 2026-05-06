from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────
#  VOLUNTEER PROFILE
# ─────────────────────────────────────────

class VolunteerProfile(models.Model):

    VOLUNTEER_TYPE_CHOICES = [
        ('medical',     'Medical Support'),
        ('education',   'Education & Tutoring'),
        ('community',   'Community Aid'),
        ('technical',   'Technical Help'),
        ('legal',       'Legal Assistance'),
        ('mental',      'Mental Health Support'),
        ('other',       'Other'),
    ]

    STATUS_CHOICES = [
        ('active',      'Active'),
        ('inactive',    'Inactive'),
        ('suspended',   'Suspended'),
    ]

    # One volunteer = one user account
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteerprofile')
    display_name    = models.CharField(max_length=100)
    volunteer_type  = models.CharField(max_length=50, choices=VOLUNTEER_TYPE_CHOICES, default='other')
    bio             = models.TextField(blank=True, null=True)
    location        = models.CharField(max_length=100, blank=True, null=True)
    phone           = models.CharField(max_length=15, blank=True, null=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_available    = models.BooleanField(default=True)

    # Stats (auto-calculated via properties)
    total_resolved  = models.PositiveIntegerField(default=0)
    total_accepted  = models.PositiveIntegerField(default=0)

    joined_at       = models.DateTimeField(default=timezone.now)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Volunteer Profile'
        verbose_name_plural = 'Volunteer Profiles'
        ordering            = ['-joined_at']

    def __str__(self):
        return f"{self.display_name} ({self.get_volunteer_type_display()})"

    @property
    def is_active(self):
        return self.status == 'active'

    def update_stats(self):
        """Call this after any request status change to keep stats fresh."""
        self.total_resolved = self.assigned_requests.filter(status='resolved').count()
        self.total_accepted = self.assigned_requests.filter(
            status__in=['accepted', 'resolved', 'assigned']
        ).count()
        self.save(update_fields=['total_resolved', 'total_accepted'])


# ─────────────────────────────────────────
#  REQUEST
# ─────────────────────────────────────────

class Request(models.Model):

    PROBLEM_TYPE_CHOICES = [
        ('medical',     'Medical Assistance'),
        ('education',   'Education & Tutoring'),
        ('community',   'Community Help'),
        ('technical',   'Technical Support'),
        ('legal',       'Legal Help'),
        ('mental',      'Mental Health'),
        ('other',       'Other'),
    ]

    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('accepted',    'Accepted'),
        ('assigned',    'Assigned'),
        ('resolved',    'Resolved'),
        ('cancelled',   'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low',     'Low'),
        ('medium',  'Medium'),
        ('high',    'High'),
    ]

    # Who made the request
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')

    # Which volunteer is handling it
    volunteer       = models.ForeignKey(
                        VolunteerProfile, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='assigned_requests'
                      )

    problem_type    = models.CharField(max_length=50, choices=PROBLEM_TYPE_CHOICES, default='other')
    description     = models.TextField()
    priority        = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    location        = models.CharField(max_length=150, blank=True, null=True)

    # Resolution details
    resolution_note = models.TextField(blank=True, null=True)
    time_spent      = models.CharField(max_length=50, blank=True, null=True)
    assign_note     = models.TextField(blank=True, null=True)

    created_at      = models.DateTimeField(default=timezone.now)
    updated_at      = models.DateTimeField(auto_now=True)
    resolved_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Request'
        verbose_name_plural = 'Requests'
        ordering            = ['-created_at']

    def __str__(self):
        return f"#{self.pk} — {self.get_problem_type_display()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-set resolved_at timestamp when status becomes resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

        # Update volunteer stats after save
        if self.volunteer:
            self.volunteer.update_stats()

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_resolved(self):
        return self.status == 'resolved'


# ─────────────────────────────────────────
#  VOLUNTEER SKILL  (optional extra)
# ─────────────────────────────────────────

class VolunteerSkill(models.Model):
    volunteer   = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='skills')
    name        = models.CharField(max_length=80)

    def __str__(self):
        return f"{self.volunteer.display_name} — {self.name}"
