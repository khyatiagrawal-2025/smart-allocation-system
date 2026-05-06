from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import VolunteerProfile, Request

@login_required
def volunteer_profile(request):
    volunteer = get_object_or_404(VolunteerProfile, user=request.user)
    return render(request, 'volunteer/volunteer_profile.html', {
        'volunteer': volunteer
    })

@login_required
def request_list(request):
    requests = Request.objects.filter(status='pending')
    return render(request, 'volunteer/request_list.html', {
        'requests': requests
    })

@login_required
def request_detail(request, pk):
    request_obj = get_object_or_404(Request, pk=pk)
    return render(request, 'volunteer/request_detail.html', {
        'request_obj': request_obj
    })

@login_required
def accept_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(Request, pk=pk)
        req.volunteer = VolunteerProfile.objects.get(user=request.user)
        req.status = 'accepted'
        req.save()
    return redirect('request_list')

@login_required
def cancel_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(Request, pk=pk)
        req.status = 'pending'
        req.volunteer = None
        req.save()
    return redirect('request_list')

@login_required
def resolve_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(Request, pk=pk)
        req.status = 'resolved'
        req.save()
    return redirect('volunteer_profile')

@login_required
def assign_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(Request, pk=pk)
        vol_id = request.POST.get('assigned_volunteer')
        req.volunteer = get_object_or_404(VolunteerProfile, pk=vol_id)
        req.status = 'assigned'
        req.save()
    return redirect('request_list')


@login_required
def volunteer_dashboard(request):
    volunteer = get_object_or_404(VolunteerProfile, user=request.user)
    requests = Request.objects.filter(volunteer=volunteer)
    return render(request, 'volunteer/volunteer_dashboard.html', {
        'volunteer': volunteer,
        'requests': requests
    })
