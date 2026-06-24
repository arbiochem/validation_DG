from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('modifier_ligne/<int:id>/', views.modifier_ligne, name='modifier_ligne'),
    path('change_statut/', views.change_statut, name='change_statut'),
    path('entete_count/', views.entete_count, name='entete_count'),
    path('etat/', views.etat, name='etat'),
    path('etat_personnalise/', views.etat_personnalise, name='etat_personnalise'),
    path('etat_personnalise_dg/', views.etat_personnalise_dg, name='etat_personnalise_dg'),
    path('afficher/', views.afficher, name='afficher'),
    path('validation/', views.validation, name='validation'),

    # ⬇️ routes fixes AVANT
    path('logout/', views.logout_view, name='logout'),
    # ⬇️ route générique TOUJOURS en dernier
    path('lignes/<str:do_piece>/', views.lignes_view, name='lignes_view'),
    
]
