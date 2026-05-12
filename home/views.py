from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'home/home.html')

def about(request):
    return render(request, 'home/about_us.html')

def contact_us(request):
    return render(request, 'home/get_support.html')

def terms(request):
    return render(request, 'home/terms.html')

def privacy_policy(request):
    return render(request, 'home/privacy_policy.html')