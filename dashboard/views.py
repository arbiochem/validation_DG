from django.shortcuts import render
from .models import FDocentete
from .models import FDOCLIGNE
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.db import connection



def logout_view(request):
    return redirect('/login/logout/')

def dashboard_home(request):
    entete = FDocentete.objects.select_related('do_tiers').filter(
        do_statut=1,
        do_piece__icontains='APA'
    ).values(
        'cbMarq',
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

@csrf_exempt
def modifier_ligne(request, id):
    # -------------------------
    # 🔥 SUPPRESSION
    # -------------------------
    if request.method == "DELETE":
        try:
            ligne = FDOCLIGNE.objects.get(pk=id)

            with connection.cursor() as cursor:
                cursor.execute("EXEC SP_DELETE @cbMarq=%s", [id])

            return JsonResponse({'success': True, 'message': 'Ligne supprimée'})
        
        except FDOCLIGNE.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ligne introuvable'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # -------------------------
    # 🔥 MISE À JOUR
    # -------------------------
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_qte = data.get('DL_QTE')
            new_montant = data.get('DL_MontantTTC')
            do_piece = data.get('do_piece')

            FDOCLIGNE.objects.get(pk=id)

            with connection.cursor() as cursor:
                cursor.execute(
                    "EXEC sp_Update_DL_QTE @cbMarq=%s, @NewQte=%s, @NewMontant=%s, @doPiece=%s",
                    [id, new_qte, new_montant, do_piece]
                )

            return JsonResponse({'success': True, 'message': 'Ligne mise à jour'})
        
        except FDOCLIGNE.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ligne introuvable'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # -------------------------
    # ❌ AUTRE MÉTHODE
    # -------------------------
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)

def change_statut(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cbMarq = data.get('cbMarq')
        if not cbMarq:
            return JsonResponse({'success': False, 'message': 'cbMarq manquant'})
        try:
            cbMarq = int(cbMarq)
        except ValueError:
            return JsonResponse({'success': False, 'message': 'cbMarq doit être un entier'})

        try:
            with connection.cursor() as cursor:
                cursor.execute("EXEC SP_Update_Type @cbMarq = %s", [cbMarq])
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

