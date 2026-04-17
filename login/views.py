from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import hashlib
import os
from django.urls import reverse
from django.shortcuts import redirect

def load_users():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(BASE_DIR, 'users.txt')
    users = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):  # ignore lignes vides et commentaires
                username, password = line.split(':')
                users[username] = hashlib.sha256(password.encode()).hexdigest()
    return users

USERS = load_users()

def home(request):
    error = request.GET.get('error')
    return render(request, 'accounts/login.html', {'error': error})

def connect(request):
    # Si déjà connecté
    if request.session.get('authenticated'):
        if request.session.get('username') == 'aina':
            return redirect(reverse('etat_personnalise'))
        return redirect('/dashboard/')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')

        if not username or not password:
            error = "Veuillez remplir tous les champs"
            return render(request, 'accounts/login.html', {'error': error})

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username in USERS and USERS[username] == password_hash:
            request.session['authenticated'] = True
            request.session['username'] = username

            # Redirection selon utilisateur
            if username == 'aina':
                return redirect(reverse('etat_personnalise'))

            next_url = request.GET.get('next') or '/dashboard/'
            return redirect(next_url)

        else:
            error = "Utilisateur ou mot de passe incorrect !!!!"

    return render(request, 'accounts/login.html', {'error': error})

def dashboard(request):
    if request.session.get('username') == 'aina':
        return redirect(reverse('etat_personnalise'))
    
    return render(request, 'dashboard/dashboard.html')

def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

def logout_view(request):
    # Supprimer la session
    request.session.flush()
    return redirect('/login/')
