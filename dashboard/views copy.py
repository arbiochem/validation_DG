from datetime import datetime, timedelta, date
from decimal import Decimal

import json

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db import connections
from sklearn.linear_model import LinearRegression
import numpy as np
from django.db.models import (
    DecimalField,
    Sum,
    F,
    Value,
    CharField,
    ExpressionWrapper,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Case,
    When
)
from django.db.models.functions import Cast, Concat, Coalesce
from .models import FDocentete
from .models import FDOCLIGNE
from .models import P_DEVISE


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
    cours = Case(
        When(Do_Cours=0, then=Value(1.0)),
        default=Cast(F('Do_Cours'), FloatField()),
        output_field=FloatField()
    )

    ligne_sum = FDOCLIGNE.objects.filter(
        do_piece=OuterRef('do_piece')
    ).values('do_piece').annotate(
        total=Sum('DL_MontantTTC')
    ).values('total')

    devise_sub = P_DEVISE.objects.filter(
        cbIndice=Cast(OuterRef('DO_Devise'), IntegerField())
    ).values('D_Intitule')[:1]

    entete = FDocentete.objects.filter(
        do_statut=1,
        do_piece__icontains='APA'
    ).annotate(
        total_ttc=Coalesce(
            Subquery(ligne_sum, output_field=FloatField()),
            Value(0.0)
        ),
        devise_libelle=Subquery(devise_sub)
    ).annotate(
        total_devise=ExpressionWrapper(
            F('total_ttc') / cours,
            output_field=FloatField()
        )
    ).values(
        'cbMarq',
        'do_piece',
        'do_ref',
        'do_tiers__ct_intitule',
        'DO_Devise',
        'total_ttc',
        'total_devise',
        'devise_libelle'
    )

    return render(request, 'dashboard/menu.html', {
        'entete': entete
    })


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def dashboard_data(request):
    with connections['default'].cursor() as cursor:
        cursor.execute("""
            SELECT 
                ent.cbMarq,
                ent.do_piece,
                ent.do_ref,
                tiers.ct_intitule           AS do_tiers__ct_intitule,
                ent.Do_Cours,
                ent.DO_Devise,
                devise.D_Intitule           AS devise_libelle,
                COALESCE(SUM(ligne.DL_MontantTTC), 0) / NULLIF(ent.Do_Cours, 0) AS total_ttc
            FROM F_DOCENTETE ent
            LEFT JOIN F_COMPTET tiers  ON tiers.ct_num   = ent.DO_Tiers
            LEFT JOIN F_DOCLIGNE ligne ON ligne.DO_Piece = ent.do_piece
            LEFT JOIN P_Devise devise  ON devise.cbIndice = ent.DO_Devise
            WHERE ent.do_statut = 1
              AND ent.do_piece LIKE '%APA%'
            GROUP BY 
                ent.cbMarq, ent.do_piece, ent.do_ref,
                tiers.ct_intitule, ent.Do_Cours,
                ent.DO_Devise, devise.D_Intitule
            ORDER BY ent.do_piece ASC
        """)
        columns = [col[0] for col in cursor.description]
        entete  = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            d['total_ttc'] = float(d['total_ttc']) if d['total_ttc'] else 0.0
            entete.append(d)

    return render(request, 'dashboard/index.html', {'entete': entete})


def lignes_view(request, do_piece):
    """Charge les lignes d'un document via AJAX"""
    try:
        lignes = FDOCLIGNE.objects.filter(do_piece=do_piece)

        try:
            entete    = FDocentete.objects.get(do_piece=do_piece)
            do_cours  = entete.Do_Cours  or 1
            do_devise = entete.DO_Devise or ""
        except FDocentete.DoesNotExist:
            do_cours  = 1
            do_devise = ""

        html = render_to_string('dashboard/ligne.html', {
            'lignes':    lignes,
            'do_piece':  do_piece,
            'do_cours':  do_cours,
            'do_devise': do_devise,
        })

        return JsonResponse({
            'success':   True,
            'html':      html,
            'do_cours':  str(do_cours),
            'do_devise': do_devise,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def etat(request):
    today = date.today()

    ca_total        = 0
    ca_total1       = 0
    ca_total_prec   = 0
    ca_total_precs  = 0
    evolution_pct   = 0

    try:
        if request.method == 'POST':
            date_debut = request.POST.get('date_debut')
            date_fin   = request.POST.get('date_fin')
        else:
            aujourd_hui = datetime.now()
            date_debut  = aujourd_hui.replace(day=1).strftime('%Y-%m-%d')
            date_fin    = aujourd_hui.strftime('%Y-%m-%d')

        print(f"Filtres - Date début: {date_debut}, Date fin: {date_fin}")

        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin   = datetime.strptime(date_fin,   '%Y-%m-%d').date()

        duree           = (date_fin - date_debut).days + 1
        date_debut_prec = date_debut - timedelta(days=duree)
        date_fin_prec   = date_fin   - timedelta(days=duree)
        date_debut_pred = date_debut + timedelta(days=duree)
        date_fin_pred   = date_fin   + timedelta(days=duree)

        # ─────────────────────────────────────────────
        # ARBIOCHEM
        # ─────────────────────────────────────────────
        ARBIO_DEPOTS = [
            'AMBOHIMANGAKELY',
            'ANALAKELY',
            'ANTANIMORA',
            'IMERINTSIATOSIKA',
            'MAHITSY',
            'DIEGO',
            'MAJUNGA',
            'TAMATAVE',
        ]

        ca_arbio_par_depot      = {}
        ca_arbio_prec_par_depot = {}

        with connections['ARBIO'].cursor() as cursor:
            for depot in ARBIO_DEPOTS:
                cursor.execute("""
                    SELECT SUM(CAHTNet)
                    FROM VENTES_AGGREGATED_DAILY
                    WHERE V_DEPOT=%s AND V_DOCDATE BETWEEN %s AND %s
                """, [depot, date_debut, date_fin])
                ca_arbio_par_depot[depot] = cursor.fetchone()[0] or 0

                cursor.execute("""
                    SELECT SUM(CAHTNet)
                    FROM VENTES_AGGREGATED_DAILY
                    WHERE V_DEPOT=%s AND V_DOCDATE BETWEEN %s AND %s
                """, [depot, date_debut_prec, date_fin_prec])
                ca_arbio_prec_par_depot[depot] = cursor.fetchone()[0] or 0

        # Variables nommées pour le template (rétrocompat)
        ca_vente  = ca_arbio_par_depot['AMBOHIMANGAKELY']
        ca_vente1 = ca_arbio_par_depot['ANALAKELY']
        ca_vente2 = ca_arbio_par_depot['ANTANIMORA']
        ca_vente3 = ca_arbio_par_depot['IMERINTSIATOSIKA']
        ca_vente4 = ca_arbio_par_depot['MAHITSY']
        ca_vente5 = ca_arbio_par_depot['DIEGO']
        ca_vente6 = ca_arbio_par_depot['MAJUNGA']
        ca_vente7 = ca_arbio_par_depot['TAMATAVE']

        ca_total      = sum(ca_arbio_par_depot.values())
        ca_total_prec = sum(ca_arbio_prec_par_depot.values())

        # Top articles ARBIO
        top_articles_arbio = []
        with connections['ARBIO'].cursor() as cursor:
            cursor.execute("""
                SELECT TOP 10
                    ART_LIB,
                    SUM(CAHTNet) AS TotalCA
                FROM [dbo].[VENTES_AGGREGATED_DAILY]
                WHERE ART_LIB <> %s
                  AND V_DOCDATE BETWEEN %s AND %s
                GROUP BY ART_LIB
                ORDER BY TotalCA DESC
            """, ['REPORT IMPAYER', date_debut, date_fin])
            for row in cursor.fetchall():
                top_articles_arbio.append({
                    'article':  row[0],
                    'total_ca': float(row[1]),
                })

        # ─────────────────────────────────────────────
        # ACTIVO (siège — CATTCNet, colonne V_DOCDATE)
        # ─────────────────────────────────────────────
        with connections['ACTIVO'].cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    SUM(CATTCNet),
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%'    THEN CATTCNet ELSE 0 END),
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%'    THEN CATTCNet ELSE 0 END),
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CATTCNet ELSE 0 END),
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CATTCNet ELSE 0 END)
                FROM VW_VENTE_CA
                WHERE V_DOCDATE BETWEEN '{date_debut}' AND '{date_fin}'
            """)
            row = cursor.fetchone()
            ca_vente_activo         = row[0] or 0
            ca_vente_activo_feed    = row[1] or 0
            ca_vente_activo_fish    = row[2] or 0
            ca_vente_activo_poussin = row[3] or 0
            ca_vente_activo_granule = row[4] or 0
            ca_total1 += ca_vente_activo

            cursor.execute(f"""
                SELECT
                    SUM(CATTCNet),
                    SUM(CASE WHEN FAGROUPE LIKE '%FEED%'    THEN CATTCNet ELSE 0 END),
                    SUM(CASE WHEN FAGROUPE LIKE '%FISH%'    THEN CATTCNet ELSE 0 END),
                    SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CATTCNet ELSE 0 END),
                    SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CATTCNet ELSE 0 END)
                FROM VW_VENTE_CA
                WHERE V_DOCDATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
            """)
            row = cursor.fetchone()
            ca_vente_activo_prec         = row[0] or 0
            ca_vente_activo_feed_prec    = row[1] or 0
            ca_vente_activo_fish_prec    = row[2] or 0
            ca_vente_activo_poussin_prec = row[3] or 0
            ca_vente_activo_granule_prec = row[4] or 0
            ca_total_precs += ca_vente_activo_prec

        # Top articles ACTIVO
        top_articles = []
        with connections['ACTIVO'].cursor() as cursor:
            cursor.execute("""
                SELECT TOP 10
                    ART_LIB,
                    SUM(CATTCNet) AS TotalCA
                FROM [dbo].[VW_VENTE_CA]
                WHERE ART_LIB <> %s
                  AND V_DOCDATE BETWEEN %s AND %s
                GROUP BY ART_LIB
                ORDER BY TotalCA DESC
            """, ['REPORT IMPAYER', date_debut, date_fin])
            for row in cursor.fetchall():
                top_articles.append({
                    'article':  row[0],
                    'total_ca': float(row[1]),
                })

        # ─────────────────────────────────────────────
        # Helper : sites avec colonne CA + LADATE
        # ─────────────────────────────────────────────
        def fetch_activofeed(conn_name):
            """Retourne (actuel_row, prec_row) pour un site ACTIVOFEED."""
            with connections[conn_name].cursor() as cur:
                cur.execute(f"""
                    SELECT
                        SUM(CA),
                        SUM(CASE WHEN FAGROUPE LIKE '%FEED%'    THEN CA ELSE 0 END),
                        SUM(CASE WHEN FAGROUPE LIKE '%FISH%'    THEN CA ELSE 0 END),
                        SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END),
                        SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END)
                    FROM VW_VENTE_CA
                    WHERE LADATE BETWEEN '{date_debut}' AND '{date_fin}'
                """)
                row_cur = cur.fetchone()

                cur.execute(f"""
                    SELECT
                        SUM(CA),
                        SUM(CASE WHEN FAGROUPE LIKE '%FEED%'    THEN CA ELSE 0 END),
                        SUM(CASE WHEN FAGROUPE LIKE '%FISH%'    THEN CA ELSE 0 END),
                        SUM(CASE WHEN FAGROUPE LIKE '%POUSSIN%' THEN CA ELSE 0 END),
                        SUM(CASE WHEN FAGROUPE LIKE '%GRANULE%' THEN CA ELSE 0 END)
                    FROM VW_VENTE_CA
                    WHERE LADATE BETWEEN '{date_debut_prec}' AND '{date_fin_prec}'
                """)
                row_prec = cur.fetchone()
            return row_cur, row_prec

        def fetch_top_activofeed(conn_name):
            top = []
            with connections[conn_name].cursor() as cur:
                cur.execute("""
                    SELECT TOP 10
                        Article,
                        SUM(CA) AS TotalCA
                    FROM [dbo].[VW_VENTE_CA]
                    WHERE Article <> %s
                      AND LADATE BETWEEN %s AND %s
                    GROUP BY Article
                    ORDER BY TotalCA DESC
                """, ['REPORT IMPAYER', date_debut, date_fin])
                for r in cur.fetchall():
                    top.append({'article': r[0], 'total_ca': float(r[1])})
            return top

        # ── ANALAKELY ──
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_ANALAKELY')
        ca_vente_activo_analakely         = row_cur[0]  or 0
        ca_vente_activo_feed_analakely    = row_cur[1]  or 0
        ca_vente_activo_fish_analakely    = row_cur[2]  or 0
        ca_vente_activo_poussin_analakely = row_cur[3]  or 0
        ca_vente_activo_granule_analakely = row_cur[4]  or 0
        ca_total1 += ca_vente_activo_analakely

        ca_vente_activo_analakely_prec         = row_prec[0] or 0
        ca_vente_activo_feed_analakely_prec    = row_prec[1] or 0
        ca_vente_activo_fish_analakely_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_analakely_prec = row_prec[3] or 0
        ca_vente_activo_granule_analakely_prec = row_prec[4] or 0
        ca_total_precs += ca_vente_activo_analakely_prec

        top_articles_analakely = fetch_top_activofeed('ACTIVOFEED_ANALAKELY')

        # ── ANTANIMORA ──
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_ANTANIMORA')
        ca_vente_activo_antanimora         = row_cur[0]  or 0
        ca_vente_activo_feed_antanimora    = row_cur[1]  or 0
        ca_vente_activo_fish_antanimora    = row_cur[2]  or 0
        ca_vente_activo_poussin_antanimora = row_cur[3]  or 0
        ca_vente_activo_granule_antanimora = row_cur[4]  or 0
        ca_total1 += ca_vente_activo_antanimora

        ca_vente_activo_antanimora_prec         = row_prec[0] or 0
        ca_vente_activo_feed_antanimora_prec    = row_prec[1] or 0
        ca_vente_activo_fish_antanimora_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_antanimora_prec = row_prec[3] or 0
        ca_vente_activo_granule_antanimora_prec = row_prec[4] or 0
        ca_total_precs += ca_vente_activo_antanimora_prec

        top_articles_antanimora = fetch_top_activofeed('ACTIVOFEED_ANTANIMORA')

        # ── DIEGO ──
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_DIEGO')
        ca_vente_activo_diego         = row_cur[0]  or 0
        ca_vente_activo_feed_diego    = row_cur[1]  or 0
        ca_vente_activo_fish_diego    = row_cur[2]  or 0
        ca_vente_activo_poussin_diego = row_cur[3]  or 0
        ca_vente_activo_granule_diego = row_cur[4]  or 0
        ca_total1 += ca_vente_activo_diego

        ca_vente_activo_diego_prec         = row_prec[0] or 0
        ca_vente_activo_feed_diego_prec    = row_prec[1] or 0
        ca_vente_activo_fish_diego_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_diego_prec = row_prec[3] or 0
        ca_vente_activo_granule_diego_prec = row_prec[4] or 0
        ca_total_precs += ca_vente_activo_diego_prec

        top_articles_diego = fetch_top_activofeed('ACTIVOFEED_DIEGO')

        # ── IMERINTSIATOSIKA ──
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_IMERINTSIATOSIKA')
        ca_vente_activo_imerintsiatosika         = row_cur[0]  or 0
        ca_vente_activo_feed_imerintsiatosika    = row_cur[1]  or 0
        ca_vente_activo_fish_imerintsiatosika    = row_cur[2]  or 0
        ca_vente_activo_poussin_imerintsiatosika = row_cur[3]  or 0
        ca_vente_activo_granule_imerintsiatosika = row_cur[4]  or 0
        ca_total1 += ca_vente_activo_imerintsiatosika

        ca_vente_activo_imerintsiatosika_prec         = row_prec[0] or 0
        ca_vente_activo_feed_imerintsiatosika_prec    = row_prec[1] or 0
        ca_vente_activo_fish_imerintsiatosika_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_imerintsiatosika_prec = row_prec[3] or 0
        ca_vente_activo_granule_imerintsiatosika_prec = row_prec[4] or 0
        ca_total_precs += ca_vente_activo_imerintsiatosika_prec

        top_articles_imerintsiatosika = fetch_top_activofeed('ACTIVOFEED_IMERINTSIATOSIKA')

        # ── MAHITSY ──
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_MAHITSY')
        ca_vente_activo_mahitsy         = row_cur[0]  or 0
        ca_vente_activo_feed_mahitsy    = row_cur[1]  or 0
        ca_vente_activo_fish_mahitsy    = row_cur[2]  or 0
        ca_vente_activo_poussin_mahitsy = row_cur[3]  or 0
        ca_vente_activo_granule_mahitsy = row_cur[4]  or 0
        ca_total1 += ca_vente_activo_mahitsy

        ca_vente_activo_mahitsy_prec         = row_prec[0] or 0
        ca_vente_activo_feed_mahitsy_prec    = row_prec[1] or 0
        ca_vente_activo_fish_mahitsy_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_mahitsy_prec = row_prec[3] or 0
        ca_vente_activo_granule_mahitsy_prec = row_prec[4] or 0
        ca_total_precs += ca_vente_activo_mahitsy_prec

        top_articles_mahitsy = fetch_top_activofeed('ACTIVOFEED_MAHITSY')

        # ── MAJUNGA ── (CORRIGÉ : bonne base + bonne colonne)
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_MAJUNGA')
        ca_vente_activo_majunga         = row_cur[0]  or 0
        ca_vente_activo_feed_majunga    = row_cur[1]  or 0
        ca_vente_activo_fish_majunga    = row_cur[2]  or 0
        ca_vente_activo_poussin_majunga = row_cur[3]  or 0
        ca_vente_activo_granule_majunga = row_cur[4]  or 0
        ca_total1 += ca_vente_activo_majunga

        ca_vente_activo_majunga_prec         = row_prec[0] or 0
        ca_vente_activo_feed_majunga_prec    = row_prec[1] or 0
        ca_vente_activo_fish_majunga_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_majunga_prec = row_prec[3] or 0
        ca_vente_activo_granule_majunga_prec = row_prec[4] or 0
        ca_total_precs += ca_vente_activo_majunga_prec

        top_articles_majunga = fetch_top_activofeed('ACTIVOFEED_MAJUNGA')

        # ── TMM ──
        row_cur, row_prec = fetch_activofeed('ACTIVOFEED_TMM')
        ca_vente_activo_tmm         = row_cur[0]  or 0
        ca_vente_activo_feed_tmm    = row_cur[1]  or 0
        ca_vente_activo_fish_tmm    = row_cur[2]  or 0
        ca_vente_activo_poussin_tmm = row_cur[3]  or 0
        ca_vente_activo_granule_tmm = row_cur[4]  or 0  # CORRIGÉ : row[4] au lieu de row[3]
        ca_total1 += ca_vente_activo_tmm

        ca_vente_activo_tmm_prec         = row_prec[0] or 0
        ca_vente_activo_feed_tmm_prec    = row_prec[1] or 0
        ca_vente_activo_fish_tmm_prec    = row_prec[2] or 0
        ca_vente_activo_poussin_tmm_prec = row_prec[3] or 0
        ca_vente_activo_granule_tmm_prec = row_prec[4] or 0  # CORRIGÉ : row[4] au lieu de row[3]
        ca_total_precs += ca_vente_activo_tmm_prec

        top_articles_tmm = fetch_top_activofeed('ACTIVOFEED_TMM')

        # ─────────────────────────────────────────────
        # Totaux finaux
        # ─────────────────────────────────────────────
        ca_totals       = ca_total  + ca_total1        # total période actuelle
        ca_total_precs1 = ca_total_prec + ca_total_precs  # total période précédente

        if ca_total_precs1:
            evolution_pct = round(((ca_totals - ca_total_precs1) / ca_total_precs1) * 100, 1)

        # ─────────────────────────────────────────────
        # Prédiction IA (régression linéaire)
        # ─────────────────────────────────────────────
        X = np.array([
            [date_debut_prec.toordinal(), date_fin_prec.toordinal()],
            [date_debut.toordinal(),      date_fin.toordinal()],
        ], dtype=float)
        y = np.array([ca_total_precs1, ca_totals])

        model = LinearRegression()
        model.fit(X, y)
        val_prediction = model.predict([[date_debut_pred.toordinal(), date_fin_pred.toordinal()]])

        # ─────────────────────────────────────────────
        # Contexte template
        # ─────────────────────────────────────────────
        def fmt(v):
            return f"{v:,.0f}".replace(',', ' ')

        context = {
            # ARBIO dépôts
            'ca_vente':  fmt(ca_vente),
            'ca_vente1': fmt(ca_vente1),
            'ca_vente2': fmt(ca_vente2),
            'ca_vente3': fmt(ca_vente3),
            'ca_vente4': fmt(ca_vente4),
            'ca_vente5': fmt(ca_vente5),
            'ca_vente6': fmt(ca_vente6),
            'ca_vente7': fmt(ca_vente7),

            # ACTIVO siège
            'ca_vente_activo':         fmt(ca_vente_activo),
            'ca_vente_activo_feed':    fmt(ca_vente_activo_feed),
            'ca_vente_activo_fish':    fmt(ca_vente_activo_fish),
            'ca_vente_activo_poussin': fmt(ca_vente_activo_poussin),
            'ca_vente_activo_granule': fmt(ca_vente_activo_granule),

            # ANALAKELY
            'ca_vente_activo_analakely':         fmt(ca_vente_activo_analakely),
            'ca_vente_activo_feed_analakely':    fmt(ca_vente_activo_feed_analakely),
            'ca_vente_activo_fish_analakely':    fmt(ca_vente_activo_fish_analakely),
            'ca_vente_activo_poussin_analakely': fmt(ca_vente_activo_poussin_analakely),
            'ca_vente_activo_granule_analakely': fmt(ca_vente_activo_granule_analakely),

            # ANTANIMORA
            'ca_vente_activo_antanimora':         fmt(ca_vente_activo_antanimora),
            'ca_vente_activo_feed_antanimora':    fmt(ca_vente_activo_feed_antanimora),
            'ca_vente_activo_fish_antanimora':    fmt(ca_vente_activo_fish_antanimora),
            'ca_vente_activo_poussin_antanimora': fmt(ca_vente_activo_poussin_antanimora),
            'ca_vente_activo_granule_antanimora': fmt(ca_vente_activo_granule_antanimora),

            # DIEGO
            'ca_vente_activo_diego':         fmt(ca_vente_activo_diego),
            'ca_vente_activo_feed_diego':    fmt(ca_vente_activo_feed_diego),
            'ca_vente_activo_fish_diego':    fmt(ca_vente_activo_fish_diego),
            'ca_vente_activo_poussin_diego': fmt(ca_vente_activo_poussin_diego),
            'ca_vente_activo_granule_diego': fmt(ca_vente_activo_granule_diego),

            # IMERINTSIATOSIKA
            'ca_vente_activo_imerintsiatosika':         fmt(ca_vente_activo_imerintsiatosika),
            'ca_vente_activo_feed_imerintsiatosika':    fmt(ca_vente_activo_feed_imerintsiatosika),
            'ca_vente_activo_fish_imerintsiatosika':    fmt(ca_vente_activo_fish_imerintsiatosika),
            'ca_vente_activo_poussin_imerintsiatosika': fmt(ca_vente_activo_poussin_imerintsiatosika),
            'ca_vente_activo_granule_imerintsiatosika': fmt(ca_vente_activo_granule_imerintsiatosika),

            # MAHITSY
            'ca_vente_activo_mahitsy':         fmt(ca_vente_activo_mahitsy),
            'ca_vente_activo_feed_mahitsy':    fmt(ca_vente_activo_feed_mahitsy),
            'ca_vente_activo_fish_mahitsy':    fmt(ca_vente_activo_fish_mahitsy),
            'ca_vente_activo_poussin_mahitsy': fmt(ca_vente_activo_poussin_mahitsy),
            'ca_vente_activo_granule_mahitsy': fmt(ca_vente_activo_granule_mahitsy),

            # MAJUNGA
            'ca_vente_activo_majunga':         fmt(ca_vente_activo_majunga),
            'ca_vente_activo_feed_majunga':    fmt(ca_vente_activo_feed_majunga),
            'ca_vente_activo_fish_majunga':    fmt(ca_vente_activo_fish_majunga),
            'ca_vente_activo_poussin_majunga': fmt(ca_vente_activo_poussin_majunga),
            'ca_vente_activo_granule_majunga': fmt(ca_vente_activo_granule_majunga),

            # TMM
            'ca_vente_activo_tmm':         fmt(ca_vente_activo_tmm),
            'ca_vente_activo_feed_tmm':    fmt(ca_vente_activo_feed_tmm),
            'ca_vente_activo_fish_tmm':    fmt(ca_vente_activo_fish_tmm),
            'ca_vente_activo_poussin_tmm': fmt(ca_vente_activo_poussin_tmm),
            'ca_vente_activo_granule_tmm': fmt(ca_vente_activo_granule_tmm),

            # Totaux & méta
            'ca_total':        ca_total,
            'ca_totals':       ca_totals,
            'ca_total1':       ca_total1,
            'ca_total_prec':   ca_total_precs1,
            'evolution_pct':   evolution_pct,
            'val_prediction':  fmt(float(val_prediction[0])),

            # Top articles
            'top_articles_arbio':           top_articles_arbio,
            'top_articles':                 top_articles,
            'top_articles_analakely':       top_articles_analakely,
            'top_articles_antanimora':      top_articles_antanimora,
            'top_articles_diego':           top_articles_diego,
            'top_articles_imerintsiatosika': top_articles_imerintsiatosika,
            'top_articles_mahitsy':         top_articles_mahitsy,
            'top_articles_majunga':         top_articles_majunga,
            'top_articles_tmm':             top_articles_tmm,

            # Dates
            'date_debut':      date_debut.strftime('%Y-%m-%d'),
            'date_fin':        date_fin.strftime('%Y-%m-%d'),
            'date_deb':        date_debut,
            'date_f':          date_fin,
            'date_debut_prec': date_debut_prec,
            'date_fin_prec':   date_fin_prec,
            'date_debut_pred': date_debut_pred,
            'date_fin_pred':   date_fin_pred,
        }

        return render(request, 'dashboard/etat.html', context)

    except Exception as e:
        print("ERREUR:", str(e))
        import traceback
        traceback.print_exc()
        return render(request, 'dashboard/etat.html')


def etat_personnalise(request):
    return render(request, 'dashboard/etat_personnalise.html')

def etat_personnalise_dg(request):

    with connection.cursor() as cursor:

        # KPI
        cursor.execute("""
            SELECT
                COUNT(DISTINCT A.AR_Ref) AS NbArticles,
                SUM(S.AS_QteSto * A.AR_PrixAch) AS ValeurStock
            FROM F_ARTSTOCK S
            INNER JOIN F_ARTICLE A
                ON S.AR_Ref = A.AR_Ref
        """)
        kpi = cursor.fetchone()

        # Ruptures
        cursor.execute("""
            SELECT COUNT(*)
            FROM F_ARTSTOCK
            WHERE AS_QteSto <= 0
        """)
        nb_ruptures = cursor.fetchone()[0]

        # Stocks faibles
        cursor.execute("""
            SELECT COUNT(*)
            FROM F_ARTSTOCK
            WHERE AS_QteSto BETWEEN 1 AND 10
        """)
        nb_alerte = cursor.fetchone()[0]

        # Stock par dépôt
        cursor.execute("""
            SELECT
                D.DE_Intitule,
                SUM(S.AS_QteSto * A.AR_PrixAch)
            FROM F_ARTSTOCK S
            INNER JOIN F_ARTICLE A
                ON A.AR_Ref = S.AR_Ref
            INNER JOIN F_DEPOT D
                ON D.DE_No = S.DE_No
            GROUP BY D.DE_Intitule
            ORDER BY 2 DESC
        """)
        stock_depots = cursor.fetchall()

        # Top 10 articles valeur
        cursor.execute("""
            SELECT TOP 10
                A.AR_Ref,
                A.AR_Design,
                SUM(S.AS_QteSto * A.AR_PrixAch) AS Valeur
            FROM F_ARTSTOCK S
            INNER JOIN F_ARTICLE A
                ON A.AR_Ref = S.AR_Ref
            GROUP BY
                A.AR_Ref,
                A.AR_Design
            ORDER BY Valeur DESC
        """)
        top_articles = cursor.fetchall()

        # Ruptures détail
        cursor.execute("""
            SELECT TOP 20
                A.AR_Ref,
                A.AR_Design,
                D.DE_Intitule
            FROM F_ARTSTOCK S
            INNER JOIN F_ARTICLE A
                ON A.AR_Ref = S.AR_Ref
            INNER JOIN F_DEPOT D
                ON D.DE_No = S.DE_No
            WHERE S.AS_QteSto <= 0
            ORDER BY A.AR_Ref
        """)
        ruptures = cursor.fetchall()

    context = {
        "nb_articles": kpi[0],
        "valeur_stock": round(kpi[1] or 0, 0),
        "nb_ruptures": nb_ruptures,
        "nb_alerte": nb_alerte,
        "stock_depots": stock_depots,
        "top_articles": top_articles,
        "ruptures": ruptures,
    }

    return render(request, 'dashboard/etat_personnalise_DG.html',context)


def entete_count(request):
    try:
        count = FDocentete.objects.filter(
            do_statut=1,
            do_piece__startswith='APA'
        ).count()
        return JsonResponse({'success': True, 'count': count})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def modifier_ligne(request, id):
    # SUPPRESSION
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

    # MISE À JOUR
    if request.method == "POST":
        try:
            data        = json.loads(request.body)
            new_qte     = data.get('DL_QTE')
            new_montant = data.get('DL_MontantTTC')
            do_piece    = data.get('do_piece')

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


ACTIVO_FEED_BASES = [
    'ACTIVO',
    'ACTIVOFEED_ANALAKELY',
    'ACTIVOFEED_ANTANIMORA',
    'ACTIVOFEED_IMERINTSIATOSIKA',
    'ACTIVOFEED_MAHITSY',
    'ACTIVOFEED_TMM',
    'ACTIVOFEED_DIEGO',
]

ACTIVO_DBS = {
    'ACTIVO',
    'ACTIVOFEED_ANALAKELY',
    'ACTIVOFEED_ANTANIMORA',
    'ACTIVOFEED_DIEGO',
    'ACTIVOFEED_IMERINTSIATOSIKA',
    'ACTIVOFEED_MAHITSY',
    'ACTIVOFEED_TMM',
}


def afficher(request):
    today      = date.today()
    date_debut = request.GET.get('date_debut', today.strftime('%Y-%m-%d'))
    date_fin   = request.GET.get('date_fin',   today.strftime('%Y-%m-%d'))
    site       = request.GET.get('site', '')
    depots     = request.GET.getlist('depots')

    print("SITE =", site, "| DEPOTS =", depots)

    rows_pdts = []

    if site == 'ARBIOCHEM':
        try:
            with connections['ARBIO'].cursor() as cursor:
                sql = """
                    SELECT
                        v.*,
                        u.U_Intitule,
                        a.AR_Ref
                    FROM VW_VENTE_CA_EP_ARTICLE v
                    JOIN F_ARTICLE a ON a.AR_Ref = v.ART_NUM
                    JOIN P_UNITE u   ON u.cbIndice = a.AR_UniteVen
                    WHERE V_DOCDATE BETWEEN %s AND %s
                    ORDER BY QteVendues DESC, CLI_INTITULE ASC
                """
                cursor.execute(sql, [date_debut, date_fin])
                rows_pdts = cursor.fetchall()
        except Exception as e:
            print(f"Erreur ARBIO : {e}")

    elif site == 'ACTIVO_FEED':
        for db_alias in ACTIVO_FEED_BASES:
            try:
                date_col = 'V_DOCDATE' if db_alias in ACTIVO_DBS else 'LADATE'
                with connections[db_alias].cursor() as cursor:
                    sql = f"""
                        SELECT
                            v.*,
                            u.U_Intitule,
                            a.AR_Ref
                        FROM VW_VENTE_CA_EP_ARTICLE v
                        JOIN F_ARTICLE a ON a.AR_Ref = v.ART_NUM
                        JOIN P_UNITE u   ON u.cbIndice = a.AR_UniteVen
                        WHERE {date_col} BETWEEN %s AND %s
                        ORDER BY CAST(v.QteVendues AS FLOAT) DESC, v.CLI_INTITULE ASC
                    """
                    cursor.execute(sql, [date_debut, date_fin])
                    rows_pdts += cursor.fetchall()
            except Exception as e:
                print(f"Erreur {db_alias} : {e}")
                continue

    return render(request, 'dashboard/etat_personnalise.html', {
        'date_debut': date_debut,
        'date_fin':   date_fin,
        'rows':       rows_pdts,
        'site':       site,
        'depots':     depots,
    })


def validation(request):
    return render(request, 'dashboard/validation.html')


def change_statut(request):
    if request.method == "POST":
        data   = json.loads(request.body)
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