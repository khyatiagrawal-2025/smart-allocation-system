from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import HelpRequest
from volunteer.models import VolunteerProfile
import google.generativeai as genai

# ================= AUTHENTICATION & CORE =================
def home_page(request):
    return render(request, 'home/home.html')

def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('role_selection')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
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
        new_req = HelpRequest.objects.create(
            requester=request.user,
            problem_category=request.POST.get('problem_category'),
            priority=request.POST.get('priority'),
            private_details=request.POST.get('private_details'),
            status='Pending'
        )
        return redirect('find_volunteers', request_id=new_req.id)
    return render(request, 'accounts/request_form.html')

@login_required
def find_volunteers(request, request_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)
    
    # Matching Engine: Find available volunteers for this category
    matched_vols = VolunteerProfile.objects.filter(
        service_role=current_req.problem_category, 
        is_available=True
    )
    
    # --- GEMINI AI INTEGRATION ---
    # PUT YOUR REAL API KEY HERE
    genai.configure(api_key="YOUR_GEMINI_API_KEY") 
    
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
    # User strictly selects one volunteer
    current_req = get_object_or_404(HelpRequest, id=request_id)
    selected_vol = get_object_or_404(VolunteerProfile, id=volunteer_id)
    
    current_req.target_volunteer = selected_vol
    current_req.status = 'Selected'
    current_req.save()
    
    return redirect('waiting_status', request_id=current_req.id)

@login_required
def waiting_status(request, request_id):
    current_req = get_object_or_404(HelpRequest, id=request_id)
    return render(request, 'accounts/user_update_status.html', {'req': current_req})