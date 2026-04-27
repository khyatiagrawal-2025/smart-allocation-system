from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import RequestForm
from .models import Volunteer, Allocation, Request


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

            # 🔥 SMART MATCHING ENGINE
            def get_best(volunteers, req, level_name):
                best_volunteer = None
                best_score = -1

                req_text = req.request_type.lower()
                req_words = set(req_text.split())

                for v in volunteers:
                    score = 0

                    # urgency scoring
                    if req.urgency.lower() == "high":
                        score += 50
                    elif req.urgency.lower() == "medium":
                        score += 30
                    else:
                        score += 10

                    # skill matching (improved)
                    volunteer_skills = v.skills.lower()
                    vol_words = set(volunteer_skills.split())

                    if req_words & vol_words:
                        score += 50
                    else:
                        continue  # skip if no match

                    # location boost
                    if (
                        v.location and req.location and
                        v.location.lower() == req.location.lower()
                    ):
                        score += 20

                    if score > best_score:
                        best_score = score
                        best_volunteer = v

                return best_volunteer, best_score, level_name


            # 1️⃣ LOCAL MATCH
            local_volunteers = Volunteer.objects.filter(
                is_available=True,
                location=req.location
            )

            best_volunteer, best_score, level = get_best(
                local_volunteers, req, "local"
            )

            # 2️⃣ CITY MATCH
            if not best_volunteer or best_score < 50:
                city_volunteers = Volunteer.objects.filter(
                    is_available=True
                ).exclude(location=req.location)

                best_volunteer, best_score, level = get_best(
                    city_volunteers, req, "city"
                )

            # 3️⃣ GLOBAL MATCH
            if not best_volunteer or best_score < 50:
                global_volunteers = Volunteer.objects.filter(
                    is_available=True
                )

                best_volunteer, best_score, level = get_best(
                    global_volunteers, req, "global"
                )

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

    return render(request, 'create_request.html', {'form': form})


def success(request):
    req = None
    allocation = None

    if request.user.is_authenticated:
        req = Request.objects.filter(user=request.user).order_by('-id').first()
        allocation = Allocation.objects.filter(request=req).first() if req else None

    return render(request, 'success.html', {
        'volunteer': allocation.volunteer if allocation else None,
        'score': allocation.score if allocation else None,
        'level': allocation.ecosystem_level if allocation else None,
        'request': req
    })

def dashboard(request):
    total_requests = Request.objects.count()
    total_volunteers = Volunteer.objects.count()
    total_allocations = Allocation.objects.count()

    recent_allocations = Allocation.objects.select_related('request', 'volunteer').order_by('-id')[:5]

    return render(request, 'dashboard.html', {
        'total_requests': total_requests,
        'total_volunteers': total_volunteers,
        'total_allocations': total_allocations,
        'recent_allocations': recent_allocations
    })