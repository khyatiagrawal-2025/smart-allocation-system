from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import HelpRequest
from volunteer.models import VolunteerProfile
import google.generativeai as genai
from django.contrib.auth.models import User
from django.contrib import messages

# ================= AUTHENTICATION & CORE =================

def register_user(request):
    if request.method == 'POST':
        fn = request.POST.get('first_name')
        ln = request.POST.get('last_name')
        u = request.POST.get('username')
        e = request.POST.get('email')
        p1 = request.POST.get('password')
        p2 = request.POST.get('confirm_password')

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists! Please choose another.")
            return redirect('register_user')

        if p1 == p2:
            user = User.objects.create_user(username=u, email=e, password=p1)
            user.first_name = fn
            user.last_name = ln
            user.save() 
            
            login(request, user)
            return redirect('role_selection')
        else:
            messages.error(request, "Passwords do not match!")
            return redirect('register_user')

    return render(request, 'accounts/register.html')

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # 🔥 SMART DECISION MAKING ENGINE 🔥
            if VolunteerProfile.objects.filter(user=user).exists():
                return redirect('volunteer_dashboard')
            elif HelpRequest.objects.filter(requester=user).exists():
                return redirect('create_request') 
            else:
                return redirect('role_selection')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('home')

@login_required
def role_selection(request):
    return render(request, 'accounts/role_selection.html')

# ================= REQUEST ENGINE =================

@login_required
def create_request(request):
    if request.method == 'POST':
        # 🔥 FIX: Yahan contact_number aur location ko save karwaya hai!
        new_req = HelpRequest.objects.create(
            requester=request.user,
            problem_category=request.POST.get('problem_category'),
            priority=request.POST.get('priority'),
            location=request.POST.get('location'),                # HTML form se Location
            contact_number=request.POST.get('phone_number'),      # HTML form se Mobile Number
            private_details=request.POST.get('private_details'),
            status='Pending'
        )
        return redirect('find_volunteers', request_id=new_req.id)
    return render(request, 'accounts/request_form.html')

@login_required
def find_volunteers(request, request_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)
    
    # Matching Engine: Sirf unko dhoondho jo online/available hain
    matched_vols = VolunteerProfile.objects.filter(
        service_role__icontains=current_req.problem_category, 
        is_available=True
    )
    
    # --- GEMINI AI INTEGRATION ---
    genai.configure(api_key="YOUR_GEMINI_API_KEY") # Yahan apni asli API key mat bhoolna
    
    ai_msg = "Scanning network for optimal matches..."
    if matched_vols.exists():
        vol_names = ", ".join([v.user.username for v in matched_vols])
        prompt = f"User needs help. Priority: {current_req.priority}, Category: {current_req.problem_category}. Available volunteers: {vol_names}. Write a 2-line urgent recommendation telling the user to select one of these volunteers. Keep it professional."
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            ai_msg = response.text
        except Exception as e:
            ai_msg = "Volunteers found! Please select one below."

    return render(request, 'accounts/available_volunteers.html', {
        'req': current_req, 
        'volunteers': matched_vols,
        'ai_recommendation': ai_msg
    })

@login_required
def select_volunteer(request, request_id, volunteer_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)
    selected_vol = get_object_or_404(VolunteerProfile, id=volunteer_id)
    
    # 🔥 FIX: Agar us do dauran Volunteer manual OFFLINE ho gaya ho, toh usko request na jaye
    if not selected_vol.is_available:
        messages.error(request, "This volunteer just went offline. Please select another.")
        return redirect('find_volunteers', request_id=current_req.id)
    
    current_req.target_volunteer = selected_vol
    current_req.status = 'Assigned' 
    current_req.save()
    
    return redirect('track_request', request_id=current_req.id)

@login_required
def track_request(request, request_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)

    if request.method == 'POST':
        if request.POST.get('status') == 'Completed':
            current_req.status = 'Completed'
            current_req.save()
            return redirect('track_request', request_id=current_req.id) 

    return render(request, 'accounts/user_update_status.html', {'req': current_req})