from django.shortcuts import render, redirect
from .models import FDocentete, FDOCLIGNE
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
from asgiref.sync import sync_to_async


# ------------------------------
# AUTH / LOGIN
# ------------------------------
def logout_view(request):
    return redirect('/login/logout/')


def require_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper


# ------------------------------
# DASHBOARD ASYNC
# ------------------------------
@require_login
async def dashboard_home(request):

    entete = await sync_to_async(list)(
        FDocentete.objects.select_related('do_tiers')
        .filter(do_statut=1, do_piece__icontains='APA')
        .values(
            'cbMarq',
            'do_piece',
            'do_ref',
            'do_tiers__ct_intitule'
        )
    )

    username = request.session.get('username', 'Utilisateur')

    context = {
        'username': username,
        'entete': entete
    }

    return render(request, 'dashboard/dashboard.html', context)


# ------------------------------
# LIGNES ASYNC
# ------------------------------
@require_login
async def lignes_view(request, do_piece):

    lignes = await sync_to_async(list)(
        FDOCLIGNE.objects.filter(do_piece=do_piece)
    )

    context = {
        'lignes': lignes
    }

    return render(request, 'dashboard/ligne.html', context)


# ------------------------------
# API : SUPPRESSION / MODIFICATION
# ------------------------------
@csrf_exempt
def modifier_ligne(request, id):

    # ---- DELETE ----
    if request.method == "DELETE":
        try:
            FDOCLIGNE.objects.get(pk=id)

            with connection.cursor() as cursor:
                cursor.execute("EXEC SP_DELETE @cbMarq=%s", [id])

            return JsonResponse({'success': True, 'message': 'Ligne supprimée'})

        except FDOCLIGNE.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ligne introuvable'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ---- UPDATE ----
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

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


# ------------------------------
# CHANGEMENT STATUT
# ------------------------------
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
