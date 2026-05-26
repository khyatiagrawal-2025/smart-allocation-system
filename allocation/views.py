from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import HelpRequest
from volunteer.models import VolunteerProfile
from google import genai
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
import random
import json
from dotenv import load_dotenv

load_dotenv()

# ================= AUTHENTICATION & CORE =================

def register_user(request):
    if request.method == 'POST':
        fn = request.POST.get('first_name')
        ln = request.POST.get('last_name')
        u  = request.POST.get('username')
        e  = request.POST.get('email')
        p1 = request.POST.get('password')
        p2 = request.POST.get('confirm_password')

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists! Please choose another.")
            return redirect('register_user')

        if p1 == p2:
            user = User.objects.create_user(username=u, email=e, password=p1)
            user.first_name = fn
            user.last_name  = ln
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


# ================= FORGOT PASSWORD — 3 STEP FLOW =================

def forgot_password(request):
    """Render the forgot password page."""
    return render(request, 'accounts/forgot_password.html')


@require_POST
def fp_send_otp(request):
    """
    STEP 1 — Receive email via AJAX POST.
    Check if user exists → generate OTP → send email → save OTP in session.
    Returns JSON.
    """
    try:
        data  = json.loads(request.body)
        email = data.get('email', '').strip().lower()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    if not email:
        return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)

    # Check if a user with this email exists
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Security: Don't reveal if email exists or not
        return JsonResponse({
            'success': True,
            'message': 'If this email is registered, you will receive a code shortly.'
        })

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # Save OTP + email in session (expires with session)
    request.session['fp_otp']   = otp
    request.session['fp_email'] = email
    request.session['fp_verified'] = False  # not verified yet

    # Send OTP email
    try:
        send_mail(
            subject='SmartAlloc — Your Password Reset Code',
            message=(
                f'Hello {user.first_name or user.username},\n\n'
                f'Your one-time password reset code is:\n\n'
                f'  {otp}\n\n'
                f'This code expires in 10 minutes. Do not share it with anyone.\n\n'
                f'If you did not request this, please ignore this email.\n\n'
                f'— SmartAlloc Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"[FP Email Error]: {e}")
        return JsonResponse({'success': False, 'error': 'Failed to send email. Please try again.'}, status=500)

    return JsonResponse({'success': True, 'message': 'OTP sent successfully.'})


@require_POST
def fp_verify_otp(request):
    """
    STEP 2 — Receive OTP via AJAX POST.
    Compare with session OTP → mark as verified if correct.
    Returns JSON.
    """
    try:
        data = json.loads(request.body)
        otp  = data.get('otp', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    session_otp   = request.session.get('fp_otp')
    session_email = request.session.get('fp_email')

    if not session_otp or not session_email:
        return JsonResponse({'success': False, 'error': 'Session expired. Please start over.'}, status=400)

    if otp != session_otp:
        return JsonResponse({'success': False, 'error': 'Incorrect OTP. Please try again.'}, status=400)

    # Mark OTP as verified in session
    request.session['fp_verified'] = True

    return JsonResponse({'success': True, 'message': 'OTP verified successfully.'})


@require_POST
def fp_reset_password(request):
    """
    STEP 3 — Receive new password via AJAX POST.
    Check session is verified → update password → clear session keys.
    Returns JSON.
    """
    try:
        data     = json.loads(request.body)
        password = data.get('password', '').strip()
        confirm  = data.get('confirm', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    # Must have completed Step 2 first
    if not request.session.get('fp_verified'):
        return JsonResponse({'success': False, 'error': 'Unauthorized. Please verify OTP first.'}, status=403)

    email = request.session.get('fp_email')
    if not email:
        return JsonResponse({'success': False, 'error': 'Session expired. Please start over.'}, status=400)

    # Validate password
    if len(password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters.'}, status=400)

    if password != confirm:
        return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)

    # Update the user's password
    try:
        user = User.objects.get(email__iexact=email)
        user.set_password(password)
        user.save()
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

    # Clean up session
    for key in ['fp_otp', 'fp_email', 'fp_verified']:
        request.session.pop(key, None)

    return JsonResponse({'success': True, 'message': 'Password updated successfully.'})


# ================= REQUEST ENGINE =================

@login_required
def create_request(request):
    if request.method == 'POST':
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

    matched_vols = VolunteerProfile.objects.filter(
        service_role__icontains=current_req.problem_category,
        is_available=True
    )

    ai_msg = "Scanning network for optimal matches..."
    if matched_vols.exists():
        vol_names = ", ".join([v.user.username for v in matched_vols])
        prompt = (
            f"User needs help. Priority: {current_req.priority}, "
            f"Category: {current_req.problem_category}. "
            f"Available volunteers: {vol_names}. "
            f"Write a 2-line urgent recommendation telling the user to select one of these volunteers. "
            f"Keep it professional."
        )
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            client  = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            ai_msg = response.text
        except Exception as e:
            print(f"AI Error: {e}")
            ai_msg = "Volunteers found! Please select one below."

    return render(request, 'accounts/available_volunteers.html', {
        'req': current_req,
        'volunteers': matched_vols,
        'ai_recommendation': ai_msg
    })


@login_required
def select_volunteer(request, request_id, volunteer_id):
    current_req  = get_object_or_404(HelpRequest, id=request_id)
    selected_vol = get_object_or_404(VolunteerProfile, id=volunteer_id)

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