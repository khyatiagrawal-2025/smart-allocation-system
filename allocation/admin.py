from django.contrib import admin
from .models import Volunteer, Request, Allocation

admin.site.register(Volunteer)
admin.site.register(Request)
admin.site.register(Allocation)