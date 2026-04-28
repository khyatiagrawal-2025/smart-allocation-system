from django.contrib import admin
from .models import UserProfile, Volunteer, Request, Allocation

admin.site.register(Volunteer)
admin.site.register(Request)
admin.site.register(Allocation)
admin.site.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dob', 'accepted_terms')
    search_fields = ('user__username', 'user__email')
    list_filter = ('accepted_terms',)