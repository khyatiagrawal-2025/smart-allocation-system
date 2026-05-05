from django.shortcuts import render, redirect
from .forms import RequestForm, UserRegistrationForm, VolunteerForm
from .models import UserProfile, Volunteer, Allocation, Request
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

# 🔒 Load environment variables
load_dotenv()

# 🔑 API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')


# 🔷 CREATE REQUEST
@login_required
def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)

        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()

            # 🧠 AI Matching Function
            def get_ai_best(volunteers, req, level_name):
                if not volunteers.exists():
                    return None, 0, level_name

                vol_data = [
                    {"id": v.id, "skills": v.skills, "location": v.location}
                    for v in volunteers
                ]

                prompt = f"""
                You are a Smart Allocation System.
                Find the BEST volunteer.

                REQUEST:
                Type: {req.request_type}
                Description: {req.description}
                Location: {req.location}
                Urgency: {req.urgency}

                VOLUNTEERS:
                {json.dumps(vol_data)}

                Return JSON:
                {{"best_volunteer_id": ID, "score": 0-100}}
                """

                try:
                    response = model.generate_content(prompt)
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    result = json.loads(clean_text)

                    best_id = result.get("best_volunteer_id")
                    score = result.get("score", 0)

                    if best_id:
                        return volunteers.get(id=best_id), score, level_name

                except Exception as e:
                    print("AI Error:", e)

                return None, 0, level_name

            # 🔁 Matching Levels
            local = Volunteer.objects.filter(is_available=True, location=req.location)
            best, score, level = get_ai_best(local, req, "local")

            if not best or score < 50:
                city = Volunteer.objects.filter(is_available=True).exclude(location=req.location)
                best, score, level = get_ai_best(city, req, "city")

            if not best or score < 50:
                global_vol = Volunteer.objects.filter(is_available=True)
                best, score, level = get_ai_best(global_vol, req, "global")

            # 💾 Save Allocation
            if best:
                Allocation.objects.create(
                    request=req,
                    volunteer=best,
                    score=score,
                    ecosystem_level=level
                )

            return redirect('success')

    else:
        form = RequestForm()

    return render(request, 'accounts/request_form.html', {'form': form})


# 🔷 SUCCESS PAGE
@login_required
def success(request):
    req = Request.objects.filter(user=request.user).order_by('-id').first()
    allocation = Allocation.objects.filter(request=req).first() if req else None

    return render(request, 'accounts/success.html', {
        'request': req,
        'volunteer': allocation.volunteer if allocation else None,
        'score': allocation.score if allocation else None,
        'level': allocation.ecosystem_level if allocation else None,
    })


# 🔷 REGISTER
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            UserProfile.objects.create(
                user=user,
                dob=form.cleaned_data.get('dob'),
                accepted_terms=form.cleaned_data.get('terms_confirmed')
            )

            login(request, user)
            return redirect('role_selection')

    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


# 🔷 DASHBOARD (IMPROVED)
@login_required
def dashboard(request):
    user = request.user

    return render(request, 'accounts/dashboard.html', {
        'user': user,
        'total_requests': Request.objects.filter(user=user).count(),
        'total_volunteers': Volunteer.objects.count(),
        'total_allocations': Allocation.objects.count(),
        'recent_allocations': Allocation.objects.select_related(
            'request', 'volunteer'
        ).order_by('-id')[:5]
    })


# 🔷 ROLE SELECTION
@login_required
def role_selection(request):
    return render(request, 'accounts/role_selection.html')


# 🔷 VOLUNTEER FORM
@login_required
def volunteer_form(request):
    if request.method == 'POST':
        form = VolunteerForm(request.POST)
        if form.is_valid():
            volunteer = form.save(commit=False)
            volunteer.user = request.user
            volunteer.save()

            return redirect('dashboard')

    else:
        form = VolunteerForm()

    return render(request, 'accounts/volunteer_form.html', {'form': form})