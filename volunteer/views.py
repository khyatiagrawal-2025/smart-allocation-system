from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import VolunteerProfile
from allocation.models import HelpRequest 

# ================= VOLUNTEER REGISTRATION =================

@login_required
def register_volunteer(request):
    if VolunteerProfile.objects.filter(user=request.user).exists():
        return redirect('volunteer_dashboard')

    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        location = request.POST.get('location')
        skills = request.POST.get('service_role')
        email_id = request.POST.get('email')

        if email_id:
            request.user.email = email_id
            request.user.save()
        
        VolunteerProfile.objects.create(
            user=request.user,
            service_role=skills,
            mobile_number=phone,
            location_description=location,
            is_available=True 
        )
        return redirect('volunteer_dashboard')
        
    return render(request, 'volunteer/volunteer_form.html') 


# ================= VOLUNTEER DASHBOARD & REQUESTS =================

@login_required
def volunteer_dashboard(request):
    try:
        my_profile = VolunteerProfile.objects.get(user=request.user)
    except VolunteerProfile.DoesNotExist:
        return redirect('register_volunteer')

    # 1. INCOMING REQUESTS (Data Locked)
    incoming_requests = HelpRequest.objects.filter(
        target_volunteer=my_profile, 
        status='Assigned'
    ).order_by('-created_at')

    # 2. ACTIVE REQUESTS (Data Unlocked)
    active_requests = HelpRequest.objects.filter(
        target_volunteer=my_profile, 
        status='Accepted'
    ).order_by('-created_at')
    
    return render(request, 'volunteer/volunteer_dashboard.html', {
        'profile': my_profile,
        'incoming_requests': incoming_requests,
        'active_requests': active_requests  # Yahan variable name update kar diya
    })

# @login_required
# def request_detail(request, request_id):
#     # REQUEST BRIEFING PAGE
#     req = get_object_or_404(HelpRequest, id=request_id)
#     return render(request, 'volunteer/request_detail.html', {'req': req})

@login_required
def accept_request(request, request_id):
    # ACTION: Volunteer Accepts the Request
    req = get_object_or_404(HelpRequest, id=request_id)
    req.status = 'Accepted'
    req.save()
    return redirect('volunteer_dashboard')

@login_required
def decline_request(request, request_id): # Naam decline_mission se decline_request kar diya
    # ACTION: Agar volunteer request decline karna chahe
    req = get_object_or_404(HelpRequest, id=request_id)
    req.status = 'Pending' 
    req.target_volunteer = None 
    req.save()
    return redirect('volunteer_dashboard')

@login_required
def mark_done(request, request_id):
    # ACTION: Request Completed
    req = get_object_or_404(HelpRequest, id=request_id)
    req.status = 'Completed' 
    req.save()
    return redirect('volunteer_dashboard')


# ================= VOLUNTEER AVAILABILITY TOGGLE =================

@login_required
def toggle_availability(request):
    if request.method == 'POST':
        my_profile = get_object_or_404(VolunteerProfile, user=request.user)
        my_profile.is_available = not my_profile.is_available
        my_profile.save()
    return redirect('volunteer_dashboard')