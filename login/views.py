
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

def logout_view(request):
    return redirect('home')

def home(request):
    return render(request, 'accounts/login.html')

def dashboard(request):
    return redirect('/dashboard/dashboard_home/')

def connect(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            error = "Veuillez remplir tous les champs"
        elif username == "admin" and password == "admin":
            return redirect('dashboard')
        else:
            error = "L'utilisateur ou mot de passe incorrect !!!!"
            return redirect('home')