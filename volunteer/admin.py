from django.contrib import admin
from .models import VolunteerProfile

@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_role', 'is_available')
    list_filter = ('is_available', 'service_role')
    search_fields = ('user__username', 'service_role')