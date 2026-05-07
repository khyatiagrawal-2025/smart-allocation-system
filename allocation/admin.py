from django.contrib import admin
from .models import HelpRequest

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'requester', 'problem_category', 'priority', 'status', 'target_volunteer', 'created_at')
    list_filter = ('status', 'priority', 'problem_category')
    search_fields = ('requester__username', 'problem_category', 'private_details')
    list_editable = ('status', 'priority')
    readonly_fields = ('created_at', 'updated_at')
