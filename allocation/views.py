from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import HelpRequest
from volunteer.models import VolunteerProfile
from google import genai
from django.contrib.auth.models import User
from django.contrib import messages
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# ================= AUTHENTICATION & CORE =================

def register_user(request):
    if request.method == 'POST':
        fn = request.POST.get('first_name')
        ln = request.POST.get('last_name')
        u = request.POST.get('username')
        e = request.POST.get('email')
        p1 = request.POST.get('password')
        p2 = request.POST.get('confirm_password')

        # Check if the username is already taken
        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists! Please choose another.")
            return redirect('register_user')

        # Verify password match before user creation
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
            
            # 1. Route to Dashboard if the user is a registered Volunteer
            if VolunteerProfile.objects.filter(user=user).exists():
                return redirect('volunteer_dashboard')
                
            # 2. Route to Request form if the user has an existing Help Request
            elif HelpRequest.objects.filter(requester=user).exists():
                return redirect('create_request') 
                
            # 3. Default route for new users without a selected role
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
        # Create a new help request and ensure location & contact data are saved
        new_req = HelpRequest.objects.create(
            requester=request.user,
            problem_category=request.POST.get('problem_category'),
            priority=request.POST.get('priority'),
            location=request.POST.get('location'),                
            contact_number=request.POST.get('phone_number'),      
            private_details=request.POST.get('private_details'),
            status='Pending'
        )
        return redirect('find_volunteers', request_id=new_req.id)
    return render(request, 'accounts/request_form.html')

@login_required
def find_volunteers(request, request_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)
    
    # Matching Engine: Filter only active and available volunteers for the specific category
    matched_vols = VolunteerProfile.objects.filter(
        service_role__icontains=current_req.problem_category, 
        is_available=True
    )
    
    # --- GEMINI AI INTEGRATION ---
    ai_msg = "Scanning network for optimal matches..."
    if matched_vols.exists():
        vol_names = ", ".join([v.user.username for v in matched_vols])
        prompt = f"User needs help. Priority: {current_req.priority}, Category: {current_req.problem_category}. Available volunteers: {vol_names}. Write a 2-line urgent recommendation telling the user to select one of these volunteers. Keep it professional."
        
        try:
            # Fetching API Key securely from .env
            api_key = os.getenv("GEMINI_API_KEY")
            
            # Initialize the new genai SDK client
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            ai_msg = response.text
            
        except Exception as e:
            # Print error to terminal if API request fails
            print(f"AI Error: {e}") 
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
    
    # Prevent assignment if the volunteer manually toggled their status to offline
    if not selected_vol.is_available:
        messages.error(request, "This volunteer just went offline. Please select another.")
        return redirect('find_volunteers', request_id=current_req.id)
    
    # Update request status to 'Assigned' and link the targeted volunteer
    current_req.target_volunteer = selected_vol
    current_req.status = 'Assigned' 
    current_req.save()
    
    return redirect('track_request', request_id=current_req.id)

@login_required
def track_request(request, request_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)

    # Handle the manual 'Mark as Completed' action triggered by the user
    if request.method == 'POST':
        if request.POST.get('status') == 'Completed':
            current_req.status = 'Completed'
            current_req.save()
            return redirect('track_request', request_id=current_req.id) 

    return render(request, 'accounts/user_update_status.html', {'req': current_req})

# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required

# Agar tera HelpRequest model kisi aur app mein hai toh use yahan import kar le
# Example: from core.models import HelpRequest

@login_required(login_url='login') 
def user_profile(request):
    my_requests = HelpRequest.objects.filter(requester=request.user).order_by('-created_at')
    user_profile_data = getattr(request.user, 'volunteer_profile', None)  # VolunteerProfile data agar exist karta hai toh
    context = {
        'user' : request.user,
        'profile': user_profile_data,
        'requests': my_requests,
    }
    return render(request, 'accounts/user_profile.html', context)