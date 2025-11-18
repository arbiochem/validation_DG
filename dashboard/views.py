from django.shortcuts import render
from .models import FDocentete
from .models import FDOCLIGNE

def logout_view(request):
    return redirect('/login/logout/')

def dashboard_home(request):
    entete = FDocentete.objects.select_related('do_tiers').filter(
        do_statut=1,
        do_piece__icontains='APA'
    ).values(
        'do_piece',
        'do_ref',
        'do_tiers__ct_intitule'
    )

    return render(request, 'dashboard/dashboard.html', {'entete': entete})

def lignes_view(request,do_piece):
    lignes = FDOCLIGNE.objects.filter(do_piece=do_piece)
    
    context = {
        'lignes': lignes,
    }
    return render(request, 'dashboard/ligne.html', context)

def ligne_modifier(request, do_piece):
    ligne = get_object_or_404(FDOCLIGNE, cbMarq=cbmarq)

    if request.method == 'POST':
        form = FDOCLIGNEForm(request.POST, instance=ligne)
        if form.is_valid():
            form.save()
            return redirect('ligne_list', do_piece=ligne.do_piece)  # redirect to your list
    else:
        form = FDOCLIGNEForm(instance=ligne)

    context = {
        'form': form,
        'ligne': ligne,
    }
    return render(request, 'dashboard/dashboard.html', context)

def ligne_supprimer(request, do_piece):
    return render(request, 'dashboard/dashboard.html', context)