import os
import json
import random
from google import genai
from dotenv import load_dotenv
from .models import HelpRequest
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from volunteer.models import VolunteerProfile
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm




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
        # 1. Retrieve map coordinates from the HTML hidden inputs
        lat_str = request.POST.get('latitude')
        lng_str = request.POST.get('longitude')

        # 2. Convert coordinates to float securely (handling empty strings just in case)
        latitude_val = float(lat_str) if lat_str else None
        longitude_val = float(lng_str) if lng_str else None

        # 3. Create a new help request and ensure location, contact, AND GPS data are saved
        new_req = HelpRequest.objects.create(
            requester=request.user,
            problem_category=request.POST.get('problem_category'),
            priority=request.POST.get('priority'),
            location=request.POST.get('location'),                
            contact_number=request.POST.get('phone_number'),      
            private_details=request.POST.get('private_details'),
            latitude=latitude_val,     # ADDED: Save exact map latitude
            longitude=longitude_val,   # ADDED: Save exact map longitude
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
                model='gemini-2.5-flash',
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
    # Retrieve the specific help request from the database
    req = get_object_or_404(HelpRequest, id=request_id)
    
    # ==========================================
    # 1. HANDLE POST REQUESTS (User Actions)
    # ==========================================
    if request.method == 'POST':
        
        # ACTION A: User selects a new volunteer from the provided list
        new_vol_id = request.POST.get('new_volunteer_id')
        if new_vol_id:
            new_vol = get_object_or_404(VolunteerProfile, id=new_vol_id)
            req.target_volunteer = new_vol
            req.status = 'Assigned'  # Revert the request status back to Assigned
            req.save()
            
            # Reload the current page to reflect changes
            return redirect(request.path)
            
        # ACTION B: User marks the mission as completed
        if request.POST.get('status') == 'Completed':
            req.status = 'Completed'
            req.save()
            
            # Reload the current page
            return redirect(request.path)

    # ==========================================
    # 2. HANDLE GET REQUESTS (Load Page Data)
    # ==========================================
    available_volunteers = None
    
    # Check if the request is pending and has been declined by at least one volunteer
    if req.status == 'Pending' and req.declined_by.count() > 0:
        
        # Fetch a list of alternate volunteers who meet the following criteria:
        # 1. They are currently marked as available
        # 2. They have NOT already declined this specific request
        available_volunteers = VolunteerProfile.objects.filter(
            is_available=True
        ).exclude(
            id__in=req.declined_by.all()
        )

    # Render the template with the request details and the list of available volunteers
    return render(request, 'accounts/user_update_status.html', {
        'req': req,
        'available_volunteers': available_volunteers
    })

@login_required(login_url='login') 
def user_profile(request):
    my_requests = HelpRequest.objects.filter(requester=request.user).order_by('-created_at')
    user_profile_data = getattr(request.user, 'volunteer_profile', None)  
    context = {
        'user' : request.user,
        'profile': user_profile_data,
        'requests': my_requests,
    }
    return render(request, 'accounts/user_profile.html', context)


# ================= SEND EMAIL TO RESET PASSWORD =================

def forgot_password(request):
    return render(request, 'accounts/forgot_password.html')

def fp_send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if not User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'No account found with this email address.'})

            otp = str(random.randint(100000, 999999))
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email

            # --- NEW EMAIL LOGIC ---
            subject = 'SmartAlloc - Secure Password Reset OTP'
            
            # send email to convert into string
            html_message = render_to_string('email/send_otp.html', {'otp': otp, 'email': email,})
            
            # show plain text when someones email not support html
            plain_message = strip_tags(html_message) 

            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email]
            
            # sending mail with html parameter
            send_mail(
                subject, 
                plain_message, 
                email_from, 
                recipient_list, 
                html_message=html_message,
                fail_silently=False
            )
            
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def fp_verify_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_otp = data.get('otp')
            
            session_otp = request.session.get('reset_otp')

            if not session_otp:
                return JsonResponse({'success': False, 'error': 'Session expired. Please request a new OTP.'})

            if str(user_otp) == str(session_otp):
                return JsonResponse({'success': True, 'message': 'OTP verified'})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid OTP. Please try again.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


def fp_reset_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_password = data.get('password')
            
            email = request.session.get('reset_email')
            
            if not email:
                return JsonResponse({'success': False, 'error': 'Unauthorized request. Start over.'})

            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            if 'reset_otp' in request.session:
                del request.session['reset_otp']
            if 'reset_email' in request.session:
                del request.session['reset_email']

            return JsonResponse({'success': True, 'message': 'Password reset successful'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})