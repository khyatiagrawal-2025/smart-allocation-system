from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import RequestForm, UserRegistrationForm
from .models import UserProfile, Volunteer, Allocation, Request
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm


# 🔒 Load environment variables from .env file
load_dotenv()

# 🔑 Fetch API Key securely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure GenAI with the fetched key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

@login_required
def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)

        if form.is_valid():
            req = form.save(commit=False)

            # 🔐 Safe user assignment
            if request.user.is_authenticated:
                req.user = request.user
            else:
                return redirect('accounts/login.html')

            req.save()

            # 🧠 AI-POWERED SMART MATCHING ENGINE (Gen AI)
            def get_ai_best(volunteers, req, level_name):
                if not volunteers.exists():
                    return None, 0, level_name

                # AI ko dene ke liye data format karo
                vol_data = [{"id": v.id, "skills": v.skills, "location": v.location} for v in volunteers]

                # AI ke liye prompt
                prompt = f"""
                You are the brain of a Smart Allocation System.
                Analyze the following Emergency Request and find the absolute BEST matching volunteer from the list based on skills, location, and urgency.

                REQUEST DETAILS:
                Type: {req.request_type}
                Description: {req.description}
                Location: {req.location}
                Urgency: {req.urgency}

                AVAILABLE VOLUNTEERS (JSON):
                {json.dumps(vol_data)}

                Return ONLY a raw JSON object in exactly this format without markdown tags:
                {{"best_volunteer_id": ID_NUMBER, "score": MATCH_PERCENTAGE_0_TO_100}}
                If no one is a good match, return {{"best_volunteer_id": null, "score": 0}}
                """

                try:
                    # Model se response generate karo
                    response = model.generate_content(prompt)
                    
                    # Clean response to ensure it's pure JSON
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    ai_result = json.loads(clean_text)

                    best_id = ai_result.get("best_volunteer_id")
                    best_score = ai_result.get("score", 0)

                    if best_id:
                        best_volunteer = volunteers.get(id=best_id)
                        return best_volunteer, best_score, level_name
                    
                    return None, 0, level_name
                except Exception as e:
                    print(f"AI Engine Error: {e}")
                    return None, 0, level_name


            # 1️⃣ LOCAL MATCH
            local_volunteers = Volunteer.objects.filter(
                is_available=True,
                location=req.location
            )
            best_volunteer, best_score, level = get_ai_best(local_volunteers, req, "local")

            # 2️⃣ CITY MATCH
            if not best_volunteer or best_score < 50:
                city_volunteers = Volunteer.objects.filter(
                    is_available=True
                ).exclude(location=req.location)
                best_volunteer, best_score, level = get_ai_best(city_volunteers, req, "city")

            # 3️⃣ GLOBAL MATCH
            if not best_volunteer or best_score < 50:
                global_volunteers = Volunteer.objects.filter(
                    is_available=True
                )
                best_volunteer, best_score, level = get_ai_best(global_volunteers, req, "global")

            # 💾 Save allocation safely
            if best_volunteer:
                Allocation.objects.create(
                    request=req,
                    volunteer=best_volunteer,
                    score=best_score,
                    ecosystem_level=level
                )

            return redirect('success')

    else:
        form = RequestForm()

    return render(request, 'accounts/create_request.html', {'form': form})

@login_required
def success(request):
    req = None
    allocation = None

    if request.user.is_authenticated:
        req = Request.objects.filter(user=request.user).order_by('-id').first()
        allocation = Allocation.objects.filter(request=req).first() if req else None

    return render(request, 'accounts/success.html', {
        'volunteer': allocation.volunteer if allocation else None,
        'score': allocation.score if allocation else None,
        'level': allocation.ecosystem_level if allocation else None,
        'request': req
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 1. Default user data save karo (Name, Email, Password)
            user = form.save()
            
            # 2. Extra data (DOB, Terms) ko UserProfile me save karo
            UserProfile.objects.create(
                user=user,
                dob=form.cleaned_data.get('dob'),
                accepted_terms=form.cleaned_data.get('terms_confirmed')
            )
            
            # 3. Automatic login karwa do
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

@login_required

def dashboard(request):
    total_requests = Request.objects.count()
    total_volunteers = Volunteer.objects.count()
    total_allocations = Allocation.objects.count()

    recent_allocations = Allocation.objects.select_related('request', 'volunteer').order_by('-id')[:5]

    return render(request, 'accounts/dashboard.html', {
        'total_requests': total_requests,
        'total_volunteers': total_volunteers,
        'total_allocations': total_allocations,
        'recent_allocations': recent_allocations
    })