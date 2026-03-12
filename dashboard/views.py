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
    ca_total1=0
    ca_total_prec=0
    evolution_pct=0
    ca_total_precs=0
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

        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()

        # Seulement ensuite :
        duree = (date_fin - date_debut).days + 1  # ligne 91
        date_debut_prec = date_debut - timedelta(days=duree)
        date_fin_prec = date_fin - timedelta(days=duree)

        # ARBIOCHEM
        with connections['ARBIO'].cursor() as cursor:
            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='AMBOHIMANGAKELY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente = cursor.fetchone()[0] or 0
            ca_total+=ca_vente

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='AMBOHIMANGAKELY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='ANALAKELY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente1 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente1

            # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='ANALAKELY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec1 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec1

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='ANALAKELY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec1 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec1

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='ANTANIMORA' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente2 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente2

             # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='ANTANIMORA' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec2 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec2

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='IMERINTSIATOSIKA' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente3 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente3

             # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='IMERINTSIATOSIKA' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec3 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec3

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='MAHITSY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente4 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente4

             # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='MAHITSY' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec4 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec4

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='DIEGO' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente5 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente5

             # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='DIEGO' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec5 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec5
            
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='MAJUNGA' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente6 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente6

             # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='MAJUNGA' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec6 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec6

            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='TAMATAVE' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut, date_fin])
            ca_vente7 = cursor.fetchone()[0] or 0
            ca_total+=ca_vente7

             # CA vente du mois en cours
            cursor.execute("""
                SELECT SUM(CAHTNet) as ca_vente
                FROM VENTES_AGGREGATED_DAILY
                WHERE V_DEPOT='TAMATAVE' AND V_DOCDATE BETWEEN %s AND %s
            """, [date_debut_prec, date_fin_prec])
            ca_vente_prec7 = cursor.fetchone()[0] or 0
            ca_total_prec+=ca_vente_prec7

       
        #ACTIVO
        with connections['ACTIVO'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CATTCNet) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CATTCNet ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CATTCNet ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CATTCNet ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CATTCNet ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE V_DOCDATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo         = row[0] or 0
            ca_vente_activo_feed    = row[1] or 0
            ca_vente_activo_fish    = row[2] or 0
            ca_vente_activo_poussin = row[3] or 0
            ca_vente_activo_granule = row[4] or 0

            ca_total1 += ca_vente_activo


            sql1 = f"""
                SELECT 
                    SUM(CATTCNet) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CATTCNet ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CATTCNet ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CATTCNet ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CATTCNet ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE V_DOCDATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql1)

            row = cursor.fetchone()
            ca_vente_activo_prec         = row[0] or 0
            ca_vente_activo_feed_prec    = row[1] or 0
            ca_vente_activo_fish_prec    = row[2] or 0
            ca_vente_activo_poussin_prec = row[3] or 0
            ca_vente_activo_granule_prec = row[4] or 0

            ca_total_precs+=ca_vente_activo_prec

        top_articles = []
        with connections['ACTIVO'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    ART_LIB,
                    SUM(CATTCNet) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE ART_LIB <> %s
                AND V_DOCDATE BETWEEN %s AND %s
                GROUP BY ART_LIB
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_ANALAKELY'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_analakely         = row[0] or 0
            ca_vente_activo_feed_analakely    = row[1] or 0
            ca_vente_activo_fish_analakely    = row[2] or 0
            ca_vente_activo_poussin_analakely = row[3] or 0
            ca_vente_activo_granule_analakely = row[4] or 0

            ca_total1 += ca_vente_activo_analakely

            sql1 = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql1)

            row = cursor.fetchone()
            ca_vente_activo_analakely_prec         = row[0] or 0
            ca_vente_activo_feed_analakely_prec    = row[1] or 0
            ca_vente_activo_fish_analakely_prec    = row[2] or 0
            ca_vente_activo_poussin_analakely_prec = row[3] or 0
            ca_vente_activo_granule_analakely_prec = row[4] or 0

            ca_total_precs+=ca_vente_activo_analakely_prec

        top_articles_analakely = []

        with connections['ACTIVOFEED_ANALAKELY'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_analakely.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_ANTANIMORA'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_antanimora        = row[0] or 0
            ca_vente_activo_feed_antanimora    = row[1] or 0
            ca_vente_activo_fish_antanimora    = row[2] or 0
            ca_vente_activo_poussin_antanimora = row[3] or 0
            ca_vente_activo_granule_antanimora = row[4] or 0

            ca_total1 += ca_vente_activo_antanimora

            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_antanimora_prec         = row[0] or 0
            ca_vente_activo_feed_antanimora_prec    = row[1] or 0
            ca_vente_activo_fish_antanimora_prec    = row[2] or 0
            ca_vente_activo_poussin_antanimora_prec = row[3] or 0
            ca_vente_activo_granule_antanimora_prec = row[4] or 0

            ca_total_precs+=ca_vente_activo_antanimora_prec

        top_articles_antanimora=[]
        with connections['ACTIVOFEED_ANTANIMORA'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_antanimora.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_DIEGO'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_diego        = row[0] or 0
            ca_vente_activo_feed_diego    = row[1] or 0
            ca_vente_activo_fish_diego    = row[2] or 0
            ca_vente_activo_poussin_diego = row[3] or 0
            ca_vente_activo_granule_diego = row[4] or 0

            ca_total1 += ca_vente_activo_diego

            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_diego_prec        = row[0] or 0
            ca_vente_activo_feed_diego_prec    = row[1] or 0
            ca_vente_activo_fish_diego_prec    = row[2] or 0
            ca_vente_activo_poussin_diego_prec = row[3] or 0
            ca_vente_activo_granule_diego_prec = row[4] or 0

            ca_total_precs += ca_vente_activo_diego_prec

        top_articles_diego=[]
        with connections['ACTIVOFEED_DIEGO'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_diego.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_IMERINTSIATOSIKA'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_imerintsiatosika        = row[0] or 0
            ca_vente_activo_feed_imerintsiatosika    = row[1] or 0
            ca_vente_activo_fish_imerintsiatosika    = row[2] or 0
            ca_vente_activo_poussin_imerintsiatosika = row[3] or 0
            ca_vente_activo_granule_imerintsiatosika = row[4] or 0

            ca_total1 += ca_vente_activo_imerintsiatosika

            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_imerintsiatosika_prec        = row[0] or 0
            ca_vente_activo_feed_imerintsiatosika_prec    = row[1] or 0
            ca_vente_activo_fish_imerintsiatosika_prec    = row[2] or 0
            ca_vente_activo_poussin_imerintsiatosika_prec = row[3] or 0
            ca_vente_activo_granule_imerintsiatosika_prec_prec = row[4] or 0

            ca_total_precs += ca_vente_activo_imerintsiatosika_prec

        top_articles_imerintsiatosika=[]
        with connections['ACTIVOFEED_IMERINTSIATOSIKA'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_imerintsiatosika.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_MAHITSY'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_mahitsy        = row[0] or 0
            ca_vente_activo_feed_mahitsy    = row[1] or 0
            ca_vente_activo_fish_mahitsy    = row[2] or 0
            ca_vente_activo_poussin_mahitsy = row[3] or 0
            ca_vente_activo_granule_mahitsy = row[4] or 0

            ca_total1 += ca_vente_activo_mahitsy

            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_mahitsy_prec        = row[0] or 0
            ca_vente_activo_feed_mahitsy_prec    = row[1] or 0
            ca_vente_activo_fish_mahitsy_prec    = row[2] or 0
            ca_vente_activo_poussin_mahitsy_prec = row[3] or 0
            ca_vente_activo_granule_mahitsy_prec = row[4] or 0

            ca_total_precs += ca_vente_activo_mahitsy_prec

        top_articles_mahitsy=[]
        with connections['ACTIVOFEED_MAHITSY'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_mahitsy.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_MAJUNGA'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_majunga        = row[0] or 0
            ca_vente_activo_feed_majunga    = row[1] or 0
            ca_vente_activo_fish_majunga    = row[2] or 0
            ca_vente_activo_poussin_majunga = row[3] or 0
            ca_vente_activo_granule_majunga = row[4] or 0

            ca_total1 += ca_vente_activo_majunga

            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_majunga_prec        = row[0] or 0
            ca_vente_activo_feed_majunga_prec    = row[1] or 0
            ca_vente_activo_fish_majunga_prec    = row[2] or 0
            ca_vente_activo_poussin_majunga_prec = row[3] or 0
            ca_vente_activo_granule_majunga_prec = row[4] or 0

            ca_total_precs += ca_vente_activo_majunga_prec

        top_articles_majunga=[]
        with connections['ACTIVOFEED_MAJUNGA'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_majunga.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        with connections['ACTIVOFEED_TMM'].cursor() as cursor:
            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_tmm        = row[0] or 0
            ca_vente_activo_feed_tmm    = row[1] or 0
            ca_vente_activo_fish_tmm    = row[2] or 0
            ca_vente_activo_poussin_tmm = row[3] or 0
            ca_vente_activo_granule_tmm = row[3] or 0

            ca_total1 += ca_vente_activo_tmm

            sql = f"""
                SELECT 
                    SUM(CA) as ca_total,
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%' THEN CA ELSE 0 END) as ca_feed,
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%' THEN CA ELSE 0 END) as ca_fish,
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END) as ca_poussin,
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END) as ca_granule
                FROM VW_VENTE_CA
                WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """
            cursor.execute(sql)

            row = cursor.fetchone()
            ca_vente_activo_tmm_prec        = row[0] or 0
            ca_vente_activo_feed_tmm_prec    = row[1] or 0
            ca_vente_activo_fish_tmm_prec    = row[2] or 0
            ca_vente_activo_poussin_tmm_prec = row[3] or 0
            ca_vente_activo_granule_tmm_prec = row[3] or 0

            ca_total_precs += ca_vente_activo_tmm_prec
        
        top_articles_tmm=[]
        with connections['ACTIVOFEED_TMM'].cursor() as cursor:
            sql = """
                SELECT TOP 10 
                    Article,
                    SUM(CA) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE Article <> %s
                AND LADATE BETWEEN %s AND %s
                GROUP BY Article
                ORDER BY TotalCA DESC
            """
            
            cursor.execute(sql, ['REPORT IMPAYER', date_debut, date_fin])
            rows = cursor.fetchall()

            for row in rows:
                top_articles_tmm.append({
                    'article': row[0],
                    'total_ca': float(row[1])
                })

        ca_totals      = ca_total  + ca_total1       # actuel total
        ca_total_precs1 = ca_total_prec + ca_total_precs  # précédent total

        evolution_pct = round(((ca_totals - ca_total_precs1) / ca_total_precs1) * 100, 1)

        # Formatage des nombres
        context = {
            'ca_vente': f"{ca_vente:,.0f}".replace(',', ' '),
            'ca_vente1': f"{ca_vente1:,.0f}".replace(',', ' '),
            'ca_vente2': f"{ca_vente2:,.0f}".replace(',', ' '),
            'ca_vente3': f"{ca_vente3:,.0f}".replace(',', ' '),
            'ca_vente4': f"{ca_vente4:,.0f}".replace(',', ' '),
            'ca_vente5': f"{ca_vente5:,.0f}".replace(',', ' '),
            'ca_vente6': f"{ca_vente6:,.0f}".replace(',', ' '),
            'ca_vente7': f"{ca_vente7:,.0f}".replace(',', ' '),
            'ca_vente_activo': f"{ca_vente_activo:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed': f"{ca_vente_activo_feed:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish': f"{ca_vente_activo_fish:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin': f"{ca_vente_activo_poussin:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule': f"{ca_vente_activo_granule:,.0f}".replace(',', ' '),
            'ca_vente_activo_analakely': f"{ca_vente_activo_analakely:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_analakely': f"{ca_vente_activo_feed_analakely:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_analakely': f"{ca_vente_activo_fish_analakely:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_analakely': f"{ca_vente_activo_poussin_analakely:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_analakely': f"{ca_vente_activo_granule_analakely:,.0f}".replace(',', ' '),
            'ca_vente_activo_antanimora': f"{ca_vente_activo_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_antanimora': f"{ca_vente_activo_feed_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_antanimora': f"{ca_vente_activo_fish_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_antanimora': f"{ca_vente_activo_poussin_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_antanimora': f"{ca_vente_activo_granule_antanimora:,.0f}".replace(',', ' '),
            'ca_vente_activo_diego': f"{ca_vente_activo_diego:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_diego': f"{ca_vente_activo_feed_diego:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_diego': f"{ca_vente_activo_fish_diego:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_diego': f"{ca_vente_activo_poussin_diego:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_diego': f"{ca_vente_activo_granule_diego:,.0f}".replace(',', ' '),
            'ca_vente_activo_imerintsiatosika': f"{ca_vente_activo_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_imerintsiatosika': f"{ca_vente_activo_feed_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_imerintsiatosika': f"{ca_vente_activo_fish_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_imerintsiatosika': f"{ca_vente_activo_poussin_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_imerintsiatosika': f"{ca_vente_activo_granule_imerintsiatosika:,.0f}".replace(',', ' '),
            'ca_vente_activo_mahitsy': f"{ca_vente_activo_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_mahitsy': f"{ca_vente_activo_feed_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_mahitsy': f"{ca_vente_activo_fish_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_mahitsy': f"{ca_vente_activo_poussin_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_mahitsy': f"{ca_vente_activo_granule_mahitsy:,.0f}".replace(',', ' '),
            'ca_vente_activo_majunga': f"{ca_vente_activo_majunga:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_majunga': f"{ca_vente_activo_feed_majunga:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_majunga': f"{ca_vente_activo_fish_majunga:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_majunga': f"{ca_vente_activo_poussin_majunga:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_majunga': f"{ca_vente_activo_granule_majunga:,.0f}".replace(',', ' '),
            'ca_vente_activo_tmm': f"{ca_vente_activo_tmm:,.0f}".replace(',', ' '),
            'ca_vente_activo_feed_tmm': f"{ca_vente_activo_feed_tmm:,.0f}".replace(',', ' '),
            'ca_vente_activo_fish_tmm': f"{ca_vente_activo_fish_tmm:,.0f}".replace(',', ' '),
            'ca_vente_activo_poussin_tmm': f"{ca_vente_activo_poussin_tmm:,.0f}".replace(',', ' '),
            'ca_vente_activo_granule_tmm': f"{ca_vente_activo_granule_tmm:,.0f}".replace(',', ' '),
            'ca_total':ca_total,
            'top_articles_analakely': top_articles_analakely,
            'top_articles_antanimora': top_articles_antanimora,
            'top_articles_diego': top_articles_diego,
            'top_articles_imerintsiatosika': top_articles_imerintsiatosika,
            'top_articles_mahitsy': top_articles_mahitsy,
            'top_articles_majunga': top_articles_majunga,
            'top_articles_tmm': top_articles_tmm,
            'top_articles': top_articles,
            'ca_totals':ca_totals,
            'ca_total1':ca_total1,
            'ca_total_prec':ca_total_precs1,
            'date_debut': date_debut.strftime('%Y-%m-%d'),
            'date_fin': date_fin.strftime('%Y-%m-%d'),
            'date_deb': date_debut,
            'date_f': date_fin,
            'date_debut_prec': date_debut_prec,
            'date_fin_prec': date_fin_prec,
            'evolution_pct':evolution_pct
        }

        return render(request, 'dashboard/etat.html', context)
        
    except Exception as e:
        print("ERREUR:", str(e))
        import traceback
        traceback.print_exc()
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

