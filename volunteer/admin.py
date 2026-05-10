from django.contrib import admin
from .models import VolunteerProfile

class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'mobile_number', 'is_available')

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email Address'

# Dhyan rakhna, poori file mein .register() wali sirf yeh ek hi line honi chahiye:
admin.site.register(VolunteerProfile, VolunteerProfileAdmin)