from django.shortcuts import render
from .models import FDocentete
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
