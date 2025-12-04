from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import hashlib

USERS = {
    'admin': hashlib.sha256('admin'.encode()).hexdigest(),
    # Ajouter d'autres utilisateurs ici
}

def home(request):
    error = request.GET.get('error')
    return render(request, 'accounts/login.html', {'error': error})

def connect(request):
    # Si déjà connecté, rediriger
    if request.session.get('authenticated'):
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Vérifier les credentials
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username in USERS and USERS[username] == password_hash:
            # Créer la session dans les cookies
            request.session['authenticated'] = True
            request.session['username'] = username
            
            # Redirection
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        else:
            return render(request, 'accounts/login.html', {
                'error': 'Utilisateur ou mot de passe incorrect !!!!'
            })
    
    return render(request, 'accounts/login.html')

def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

def logout_view(request):
    # Supprimer la session
    request.session.flush()
    return redirect('/login/')
