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
                return redirect('login')

            req.save()

            # 🧠 AI Matching Function
            def get_ai_best(volunteers, req, level_name):
                if not volunteers.exists():
                    return None, 0, level_name

                vol_data = [{"id": v.id, "skills": v.skills, "location": v.location} for v in volunteers]

                prompt = f"""
                You are the brain of a Smart Allocation System.
                Analyze the following Emergency Request and find the BEST matching volunteer.

                REQUEST:
                Type: {req.request_type}
                Description: {req.description}
                Location: {req.location}
                Urgency: {req.urgency}

                VOLUNTEERS:
                {json.dumps(vol_data)}

                Return JSON only:
                {{"best_volunteer_id": ID, "score": 0-100}}
                """

                try:
                    response = model.generate_content(prompt)
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    ai_result = json.loads(clean_text)

                    best_id = ai_result.get("best_volunteer_id")
                    score = ai_result.get("score", 0)

                    if best_id:
                        return volunteers.get(id=best_id), score, level_name

                    return None, 0, level_name

                except Exception as e:
                    print(f"AI Error: {e}")
                    return None, 0, level_name

            # Matching Levels
            local_volunteers = Volunteer.objects.filter(is_available=True, location=req.location)
            best_volunteer, best_score, level = get_ai_best(local_volunteers, req, "local")

            if not best_volunteer or best_score < 50:
                city_volunteers = Volunteer.objects.filter(is_available=True).exclude(location=req.location)
                best_volunteer, best_score, level = get_ai_best(city_volunteers, req, "city")

            if not best_volunteer or best_score < 50:
                global_volunteers = Volunteer.objects.filter(is_available=True)
                best_volunteer, best_score, level = get_ai_best(global_volunteers, req, "global")

            # Save allocation
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

    # ✅ UPDATED TEMPLATE NAME
    return render(request, 'accounts/request_form.html', {'form': form})


@login_required
def success(request):
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
            user = form.save()

            UserProfile.objects.create(
                user=user,
                dob=form.cleaned_data.get('dob'),
                accepted_terms=form.cleaned_data.get('terms_confirmed')
            )

            login(request, user)

            # ✅ BETTER FLOW
            return redirect('role_selection')

    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html', {
        'total_requests': Request.objects.count(),
        'total_volunteers': Volunteer.objects.count(),
        'total_allocations': Allocation.objects.count(),
        'recent_allocations': Allocation.objects.select_related('request', 'volunteer').order_by('-id')[:5]
    })


def role_selection(request):
    return render(request, 'accounts/role_selection.html')