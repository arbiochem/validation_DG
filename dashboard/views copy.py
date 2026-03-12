from django.shortcuts import render, redirect
from .models import FDocentete
from .models import FDOCLIGNE
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.db import connections
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta

def logout_view(request):
    return redirect('/login')

def require_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper

@require_login
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

    username = request.session.get('username', 'Utilisateur')
    
    context = {
        'username': username,
        'entete':entete
    }
    return render(request, 'dashboard/menu.html', context)

def dashboard_data(request):
    # Données qui vont changer
    entete = list(FDocentete.objects.select_related('do_tiers').filter(
        do_statut=1,
        do_piece__icontains='APA'
    ).values('cbMarq', 'do_piece', 'do_ref', 'do_tiers__ct_intitule'))
    return JsonResponse({'entete': entete})

def lignes_view(request,do_piece):
    """Charge les lignes d'un document via AJAX"""
    try:
        # Récupérer les lignes du document
        lignes = FDOCLIGNE.objects.filter(do_piece=do_piece)
        
        # Rendre le template avec les lignes
        html = render_to_string('dashboard/ligne.html', {
            'lignes': lignes,
            'do_piece': do_piece
        })
        
        return JsonResponse({
            'success': True,
            'html': html
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

def etat(request):
    ca_total=0
    try:
        if request.method == 'POST':
            date_debut = request.POST.get('date_debut')
            date_fin = request.POST.get('date_fin')
        else:
            # Par défaut : début du mois en cours à aujourd'hui
            aujourd_hui = datetime.now()
            date_debut = aujourd_hui.replace(day=1).strftime('%Y-%m-%d')
            date_fin = aujourd_hui.strftime('%Y-%m-%d')

        print(f"Filtres - Date début: {date_debut}, Date fin: {date_fin}")

        # Calculer la période précédente
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d')
        duree = (date_fin_obj - date_debut_obj).days
        
        date_debut_precedent = (date_debut_obj - timedelta(days=duree + 1)).strftime('%Y-%m-%d')
        date_fin_precedent = (date_debut_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"Période précédente: {date_debut_precedent} à {date_fin_precedent}")

        # Calculer les KPIs
        with connections['ARBIO'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='AMBOHIMANGAKELY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente = cursor.fetchone()[0] or 0
            ca_total+=ca_vente
            
            print(f"CA Vente période actuelle: {ca_vente}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente_precedent
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VENTES_AGGREGATED_DAILY
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent > 0:
            kpi_vente = round(((ca_vente - ca_vente_mois_precedent) / ca_vente_mois_precedent) * 100, 2)
        else:
            kpi_vente = 0

        with connections['ACTIVO'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo
            
            print(f"CA Vente période actuelle: {ca_vente}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo > 0:
            kpi_vente_activo = round(((ca_vente_activo - ca_vente_mois_precedent_activo) / ca_vente_mois_precedent_activo) * 100, 2)
        else:
            kpi_vente_activo = 0

        with connections['ACTIVOFEED_ANALAKELY'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo_analakely = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo_analakely
            
            print(f"CA Vente période actuelle: {ca_vente_activo_analakely}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo_analakely = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo_analakely}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo > 0:
            kpi_vente_activo_analakely = round(((ca_vente_activo_analakely - ca_vente_mois_precedent_activo_analakely) / ca_vente_mois_precedent_activo_analakely) * 100, 2)
        else:
            kpi_vente_activo_analakely = 0

        with connections['ACTIVOFEED_MAHITSY'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo_mahitsy = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo_mahitsy
            
            print(f"CA Vente période actuelle: {ca_vente_activo_mahitsy}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo_mahitsy = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo_mahitsy}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo_mahitsy > 0:
            kpi_vente_activo_mahitsy = round(((ca_vente_activo_mahitsy - ca_vente_mois_precedent_activo_mahitsy) / ca_vente_mois_precedent_activo_mahitsy) * 100, 2)
        else:
            kpi_vente_activo_mahitsy = 0

        with connections['ACTIVOFEED_ANTANIMORA'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo_antanimora = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo_antanimora
            
            print(f"CA Vente période actuelle: {ca_vente_activo_antanimora}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo_antanimora = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo_antanimora}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo > 0:
            kpi_vente_activo_antanimora = round(((ca_vente_activo_antanimora - ca_vente_mois_precedent_activo_antanimora) / ca_vente_mois_precedent_activo_antanimora) * 100, 2)
        else:
            kpi_vente_activo_antanimora = 0

        with connections['ACTIVOFEED_DIEGO'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo_diego = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo_diego

            print(f"CA Vente période actuelle: {ca_vente_activo_diego}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo_diego = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo_diego}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo > 0:
            kpi_vente_activo_diego = round(((ca_vente_activo_diego - ca_vente_mois_precedent_activo_diego) / ca_vente_mois_precedent_activo_diego) * 100, 2)
        else:
            kpi_vente_activo_diego = 0
        
        with connections['ACTIVOFEED_IMERINTSIATOSIKA'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo_imerintsiatosika = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo_imerintsiatosika

            print(f"CA Vente période actuelle: {ca_vente_activo_imerintsiatosika}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo_imerintsiatosika = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo_imerintsiatosika}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo_imerintsiatosika > 0:
            kpi_vente_activo_imerintsiatosika = round(((ca_vente_activo_imerintsiatosika - ca_vente_mois_precedent_activo_imerintsiatosika) / ca_vente_mois_precedent_activo_imerintsiatosika) * 100, 2)
        else:
            kpi_vente_activo_imerintsiatosika = 0

        with connections['ACTIVOFEED_TMM'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente_activo_tmm = cursor.fetchone()[0] or 0
            ca_total+=ca_vente_activo_tmm
            
            print(f"CA Vente période actuelle: {ca_vente_activo_tmm}")
            
            # CA vente du mois précédent
            cursor.execute("""
                SELECT SUM(CATTCNet) as ca_vente
                FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_precedent, date_fin_precedent])
            ca_vente_mois_precedent_activo_tmm = cursor.fetchone()[0] or 0
            
            print(f"CA Vente période précédente: {ca_vente_mois_precedent_activo_tmm}")

            # Récupérer toutes les données pour les graphiques
            cursor.execute("""
                SELECT * FROM VW_VENTE_CA_EP_ARTICLE
                WHERE V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            
            colonnes = [col[0] for col in cursor.description]
            resultats = [
                dict(zip(colonnes, row))
                for row in cursor.fetchall()
            ]

        # Calculer les KPIs
        if ca_vente_mois_precedent_activo_tmm > 0:
            kpi_vente_activo_tmm = round(((ca_vente_activo_tmm - ca_vente_mois_precedent_activo_tmm) / ca_vente_mois_precedent_activo_tmm) * 100, 2)
        else:
            kpi_vente_activo_tmm = 0

        # Formatage des nombres
        context = {
            'ca_vente': f"{ca_vente:,.0f}".replace(',', ' '),
            'ca_total':ca_total,
            'ca_vente_mois_precedent': f"{ca_vente_mois_precedent:,.0f}".replace(',', ' '),
            'ca_vente_activo': f"{ca_vente_activo:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo': f"{ca_vente_mois_precedent_activo:,.0f}".replace(',', ' '),
            'ca_vente_activo_analakely': f"{ca_vente_activo_analakely:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo_analakely': f"{ca_vente_mois_precedent_activo_analakely:,.0f}".replace(',', ' '),
            'ca_vente_activo_antanimora': f"{ca_vente_activo_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo_antanimora': f"{ca_vente_mois_precedent_activo_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_activo_diego': f"{ca_vente_activo_diego:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo_diego': f"{ca_vente_mois_precedent_activo_diego:,.0f}".replace(',', ' '),
            'ca_vente_activo_mahitsy': f"{ca_vente_activo_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo_mahitsy': f"{ca_vente_mois_precedent_activo_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_activo_imerintsiatosika': f"{ca_vente_activo_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo_imerintsiatosika': f"{ca_vente_mois_precedent_activo_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_activo_tmm': f"{ca_vente_activo_tmm:,.0f}".replace(',', ' '),
            'ca_vente_mois_precedent_activo_tmm': f"{ca_vente_mois_precedent_activo_tmm:,.0f}".replace(',', ' '),
            'kpi_vente': f"{'+' if kpi_vente > 0 else ''}{kpi_vente}%",
            'kpi_vente_val': float(kpi_vente),
            'kpi_vente_activo': f"{'+' if kpi_vente_activo > 0 else ''}{kpi_vente_activo}%",
            'kpi_vente_val_activo': float(kpi_vente_activo),
            'kpi_vente_activo_analakely': f"{'+' if kpi_vente_activo_analakely > 0 else ''}{kpi_vente_activo_analakely}%",
            'kpi_vente_val_activo_analakely': float(kpi_vente_activo_analakely),
            'kpi_vente_activo_antanimora': f"{'+' if kpi_vente_activo_antanimora > 0 else ''}{kpi_vente_activo_antanimora}%",
            'kpi_vente_val_activo_antanimora': float(kpi_vente_activo_antanimora),
            'kpi_vente_activo_diego': f"{'+' if kpi_vente_activo_diego > 0 else ''}{kpi_vente_activo_diego}%",
            'kpi_vente_val_activo_diego': float(kpi_vente_activo_diego),
            'kpi_vente_activo_mahitsy': f"{'+' if kpi_vente_activo_mahitsy > 0 else ''}{kpi_vente_activo_mahitsy}%",
            'kpi_vente_val_activo_mahitsy': float(kpi_vente_activo_mahitsy),
            'kpi_vente_activo_imerintsiatosika': f"{'+' if kpi_vente_activo_imerintsiatosika > 0 else ''}{kpi_vente_activo_imerintsiatosika}%",
            'kpi_vente_val_activo_imerintsiatosika': float(kpi_vente_activo_imerintsiatosika),
            'kpi_vente_activo_tmm': f"{'+' if kpi_vente_activo_tmm > 0 else ''}{kpi_vente_activo_tmm}%",
            'kpi_vente_val_activo_tmm': float(kpi_vente_activo_tmm),
            'resultats': resultats,
            'date_debut': date_debut,
            'date_fin': date_fin,
        }

        return render(request, 'dashboard/etat.html', context)
        
    except Exception as e:
        print("ERREUR:", str(e))
        import traceback
        traceback.print_exc()
        
        # Retourner un contexte vide en cas d'erreur
        aujourd_hui = datetime.now()
        context = {
            'ca_vente': '0',
            'ca_vente_mois_precedent': '0',
            'kpi_vente': '0%',
            'ca_achat': '0',
            'ca_achat_mois_precedent': '0',
            'kpi_achat': '0%',
            'recouvrement': '0',
            'resultats': [],
            'error': str(e),
            'date_debut': aujourd_hui.replace(day=1).strftime('%Y-%m-%d'),
            'date_fin': aujourd_hui.strftime('%Y-%m-%d'),
        }
        return render(request, 'dashboard/etat.html', context)

def entete_count(request):
    try:
        # Compter TOUS les documents avec DO_Statut=1
        count = FDocentete.objects.filter(
            do_statut=1,
            do_piece__startswith='APA'
        ).count()
        
        print(f"✅ Count trouvé: {count}")  # DEBUG
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")  # DEBUG
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

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

def validation(request):
    return render(request, 'dashboard/validation.html')

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

