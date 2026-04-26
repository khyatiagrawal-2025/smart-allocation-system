from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import RequestForm
from .models import Volunteer, Allocation


def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)

        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()

            # 🔥 SMART MATCHING ENGINE
            def get_best(volunteers, req, level_name):
                best_volunteer = None
                best_score = -1

                req_text = req.request_type.lower()

                for v in volunteers:
                    score = 0

                    # urgency scoring
                    if req.urgency.lower() == "high":
                        score += 50
                    elif req.urgency.lower() == "medium":
                        score += 30
                    else:
                        score += 10

                    # skill matching
                    volunteer_skills = v.skills.lower()

                    if any(word in volunteer_skills for word in req_text.split()):
                        score += 50
                    else:
                        continue  # skip if no skill match

                    # location match boost
                    if v.location and req.location and v.location.lower() == req.location.lower():
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

            best_volunteer, best_score, level = get_best(local_volunteers, req, "local")

            # 2️⃣ CITY MATCH
            if not best_volunteer or best_score < 50:
                city_volunteers = Volunteer.objects.filter(is_available=True)
                best_volunteer, best_score, level = get_best(city_volunteers, req, "city")

            # 3️⃣ GLOBAL MATCH
            if not best_volunteer or best_score < 50:
                global_volunteers = Volunteer.objects.all()
                best_volunteer, best_score, level = get_best(global_volunteers, req, "global")


            # Save allocation safely
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
    # Get latest allocation safely
    allocation = Allocation.objects.order_by('-id').first()

    return render(request, 'success.html', {
        'volunteer': allocation.volunteer if allocation else None,
        'score': allocation.score if allocation else None,
        'level': allocation.ecosystem_level if allocation else None,
        'request': allocation.request if allocation else None
    })