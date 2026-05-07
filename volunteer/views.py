from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import VolunteerProfile
from allocation.models import HelpRequest

def register_volunteer(request):
    if VolunteerProfile.objects.filter(user=request.user).exists():
        return redirect('volunteer_dashboard')

@login_required
def register_volunteer(request):
    if request.method == 'POST':
        # Create profile and make them active
        VolunteerProfile.objects.create(
            user=request.user,
            service_role=request.POST.get('service_role'),
            is_available=True if request.POST.get('is_available') else False
        )
        return redirect('volunteer_dashboard')
    return render(request, 'volunteer/volunteer_form.html')

@login_required
def volunteer_dashboard(request):
    try:
        my_profile = request.user.volunteer_profile
        # ONLY show requests where the user specifically selected THIS volunteer
        pending_requests = HelpRequest.objects.filter(target_volunteer=my_profile, status='Selected').order_by('-created_at')
        return render(request, 'volunteer/request_list.html', {'requests': pending_requests})
    except:
        return redirect('register_volunteer_profile')

@login_required
def request_detail(request, request_id):
    # Privacy Lock ON: Volunteer reads the problem but no private details
    req = get_object_or_404(HelpRequest, id=request_id)
    return render(request, 'volunteer/request_detail.html', {'req': req})

@login_required
def accept_request(request, request_id):
    # Action: Volunteer Hits Accept -> Unlocks Data
    req = get_object_or_404(HelpRequest, id=request_id)
    req.status = 'Accepted'
    req.save()
    return redirect('resolve_mission', request_id=req.id)

@login_required
def resolve_mission(request, request_id):
    # Privacy Lock OFF: Render the unlocked page
    req = get_object_or_404(HelpRequest, id=request_id)
    return render(request, 'volunteer/resolve_assign.html', {'req': req})

@login_required
def mark_done(request, request_id):
    # Action: Mission Accomplished
    req = get_object_or_404(HelpRequest, id=request_id)
    req.status = 'Resolved'
    req.save()
    return redirect('volunteer_dashboard')

@login_required
def volunteer_profile(request):
    my_profile = get_object_or_404(VolunteerProfile, user=request.user)
    
    if request.method == 'POST':
        # Toggle Online/Offline
        my_profile.is_available = True if request.POST.get('is_available') else False
        my_profile.save()
        return redirect('volunteer_profile')
        
    return render(request, 'volunteer/volunteer_profile.html', {'profile': my_profile})